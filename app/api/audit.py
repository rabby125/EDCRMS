from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.log_model import AuditLog, LoginLog
from app.models.user_model import User
from app.core.permissions import require_role

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
def list_audit_logs(module: Optional[str] = Query(None), user_id: Optional[int] = Query(None),
                     skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role("Admin"))):
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/login-logs")
def list_login_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role("Admin"))):
    return db.query(LoginLog).order_by(LoginLog.timestamp.desc()).offset(skip).limit(limit).all()
