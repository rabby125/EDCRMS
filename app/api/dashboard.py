from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.infrastructure_model import DataCenter, Room, Rack
from app.models.device_model import Device
from app.models.user_model import User
from app.models.log_model import AuditLog
from app.core.permissions import require_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    total_datacenters = db.query(func.count(DataCenter.id)).scalar()
    total_rooms = db.query(func.count(Room.id)).scalar()
    racks = db.query(Rack).all()
    total_racks = len(racks)
    total_devices = db.query(func.count(Device.id)).scalar()
    online_devices = db.query(func.count(Device.id)).filter(Device.status == "online").scalar()
    offline_devices = db.query(func.count(Device.id)).filter(Device.status == "offline").scalar()
    critical_alerts = db.query(func.count(Device.id)).filter(Device.status == "alert").scalar()

    total_capacity_u = sum(r.height_u for r in racks) or 0
    total_used_u = sum(r.used_u() for r in racks) or 0
    usage_percent = round((total_used_u / total_capacity_u) * 100, 1) if total_capacity_u else 0
    free_u = total_capacity_u - total_used_u

    warranty_cutoff = date.today() + timedelta(days=30)
    warranty_alerts = db.query(func.count(Device.id)).filter(
        Device.warranty_exp.isnot(None), Device.warranty_exp <= warranty_cutoff
    ).scalar()

    active_users = db.query(func.count(User.id)).filter(User.status == "active").scalar()

    return {
        "total_data_centers": total_datacenters,
        "total_rooms": total_rooms,
        "total_racks": total_racks,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "rack_usage_percent": usage_percent,
        "free_rack_space_u": free_u,
        "warranty_expiring_soon": warranty_alerts,
        "active_users": active_users,
        "system_critical_alerts": critical_alerts,
    }


@router.get("/recent-activities")
def recent_activities(limit: int = 10, db: Session = Depends(get_db),
                       current_user: User = Depends(require_role("Viewer"))):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/device-status-chart")
def device_status_chart(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    rows = db.query(Device.status, func.count(Device.id)).group_by(Device.status).all()
    return {"labels": [r[0] for r in rows], "values": [r[1] for r in rows]}
