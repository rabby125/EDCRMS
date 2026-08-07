from sqlalchemy.orm import Session
from fastapi import Request

from app.models.log_model import AuditLog


def log_action(db: Session, user_id: int, module: str, action: str, description: str = "", request: Request = None):
    ip = request.client.host if request and request.client else None
    entry = AuditLog(
        user_id=user_id,
        module=module,
        action=action,
        description=description,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
