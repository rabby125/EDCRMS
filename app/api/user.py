from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_model import User, Role
from app.models.log_model import AuditLog, LoginLog, Notification
from app.schemas.user_schema import UserCreate, UserUpdate, UserOut, ChangePasswordRequest
from app.core.security import hash_password, verify_password
from app.core.permissions import require_role, ROLE_LEVELS
from app.middleware.auth_middleware import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/api/users", tags=["User Management"])


def _assert_can_assign_role(db: Session, current_user: User, role_id: int) -> None:
    """Stop an Admin (or lower) from creating/promoting a user to a role
    equal to or higher than their own. Only Super Admin may assign
    Admin/Super Admin roles."""
    if role_id is None:
        return

    target_role = db.query(Role).filter(Role.id == role_id).first()
    if not target_role:
        raise HTTPException(status_code=400, detail="Invalid role_id")

    current_role_name = current_user.role.name if current_user.role else "Viewer"
    current_level = ROLE_LEVELS.get(current_role_name, 0)
    target_level = ROLE_LEVELS.get(target_role.name, 0)

    if current_role_name != "Super Admin" and target_level >= current_level:
        raise HTTPException(
            status_code=403,
            detail="You cannot assign a role equal to or higher than your own.",
        )


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_role("Admin"))):
    return db.query(User).all()


@router.post("/", response_model=UserOut)
def create_user(payload: UserCreate, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Admin"))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    _assert_can_assign_role(db, current_user, payload.role_id)

    user = User(
        name=payload.name,
        username=payload.username,
        password=hash_password(payload.password),
        role_id=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "user", "create", f"Created user {user.username}", request)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role_id is not None:
        _assert_can_assign_role(db, current_user, payload.role_id)

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "user", "update", f"Updated user {user.username}", request)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Super Admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    # This user may already have audit/login/notification history pointing to
    # their id via a foreign key. MySQL blocks the delete unless those
    # references are cleared first. We keep the log rows (for history) but
    # detach them from the deleted user by setting user_id to NULL.
    db.query(AuditLog).filter(AuditLog.user_id == user_id).update({"user_id": None})
    db.query(LoginLog).filter(LoginLog.user_id == user_id).update({"user_id": None})
    db.query(Notification).filter(Notification.user_id == user_id).update({"user_id": None})

    username = user.username
    db.delete(user)
    db.commit()
    log_action(db, current_user.id, "user", "delete", f"Deleted user {username} (id {user_id})", request)
    return {"message": "User deleted"}


@router.put("/me/password")
def change_my_password(payload: ChangePasswordRequest, request: Request, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password = hash_password(payload.new_password)
    db.commit()
    log_action(db, current_user.id, "user", "update", "Changed own password", request)
    return {"message": "Password updated successfully"}