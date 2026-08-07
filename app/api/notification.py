from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.log_model import Notification
from app.models.user_model import User
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/")
def list_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(
        Notification.created_at.desc()
    ).all()


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == current_user.id
    ).first()
    if note:
        note.is_read = True
        db.commit()
    return {"message": "ok"}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False  # noqa: E712
    ).count()
    return {"unread": count}
