from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_model import User
from app.models.log_model import LoginLog
from app.core.security import verify_password, create_access_token
from app.schemas.user_schema import LoginRequest, TokenResponse, UserOut
from app.middleware.auth_middleware import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.password):
        ip = request.client.host if request.client else None
        db.add(LoginLog(user_id=user.id if user else None, ip_address=ip, status="failed"))
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is inactive")

    token = create_access_token(data={"sub": str(user.id)})

    ip = request.client.host if request.client else None
    db.add(LoginLog(user_id=user.id, ip_address=ip, status="success"))
    db.commit()
    log_action(db, user.id, "auth", "login", "User logged in", request)

    return TokenResponse(
        access_token=token,
        user_name=user.name,
        role=user.role.name if user.role else None,
    )


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log_action(db, current_user.id, "auth", "logout", "User logged out", request)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user