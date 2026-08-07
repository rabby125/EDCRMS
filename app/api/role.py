from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_model import Role, User
from app.schemas.user_schema import RoleCreate, RoleOut
from app.core.permissions import require_role

router = APIRouter(prefix="/api/roles", tags=["Role Management"])


@router.get("/", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    return db.query(Role).all()


@router.post("/", response_model=RoleOut)
def create_role(payload: RoleCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Super Admin"))):
    if db.query(Role).filter(Role.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Role already exists")
    role = Role(**payload.dict())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Super Admin"))):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role: {user_count} user(s) are still assigned to it. Reassign those users first.",
        )
    db.delete(role)
    db.commit()
    return {"message": "Role deleted"}