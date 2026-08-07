from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.device_model import DeviceType, Device
from app.models.user_model import User
from app.schemas.device_schema import DeviceTypeCreate, DeviceTypeOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/device-types", tags=["Device Type"])


@router.get("/", response_model=List[DeviceTypeOut])
def list_device_types(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    return db.query(DeviceType).all()


@router.post("/", response_model=DeviceTypeOut)
def create_device_type(payload: DeviceTypeCreate, request: Request, db: Session = Depends(get_db),
                        current_user: User = Depends(require_role("Engineer"))):
    if db.query(DeviceType).filter(DeviceType.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Device type already exists")
    obj = DeviceType(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "device_type", "create", f"Created device type {obj.name}", request)
    return obj


@router.delete("/{item_id}")
def delete_device_type(item_id: int, request: Request, db: Session = Depends(get_db),
                        current_user: User = Depends(require_role("Admin"))):
    obj = db.query(DeviceType).filter(DeviceType.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Device type not found")
    db.query(Device).filter(Device.device_type_id == item_id).update({"device_type_id": None})
    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "device_type", "delete", f"Deleted device type id {item_id}", request)
    return {"message": "Device type deleted"}