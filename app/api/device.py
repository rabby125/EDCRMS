from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.device_model import Device
from app.models.infrastructure_model import Rack
from app.models.cable_model import Cable
from app.models.asset_model import Asset
from app.models.user_model import User
from app.schemas.device_schema import DeviceCreate, DeviceUpdate, DeviceOut, DeviceMove
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/devices", tags=["Device"])


def _check_u_space(db: Session, rack_id: int, start_u: int, height_u: int, exclude_device_id: Optional[int] = None):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")

    end_u = start_u + height_u - 1
    if start_u < 1 or end_u > rack.height_u:
        raise HTTPException(status_code=400, detail=f"Device does not fit within rack's {rack.height_u}U capacity")

    for device in rack.devices:
        if exclude_device_id and device.id == exclude_device_id:
            continue
        d_end = device.start_u + device.height_u - 1
        if start_u <= d_end and end_u >= device.start_u:
            raise HTTPException(
                status_code=400,
                detail=f"U-space conflict: overlaps with device '{device.hostname}' (U{device.start_u}-U{d_end})",
            )


@router.get("/", response_model=List[DeviceOut])
def list_devices(rack_id: Optional[int] = Query(None), status_filter: Optional[str] = Query(None, alias="status"),
                  search: Optional[str] = Query(None), skip: int = 0, limit: int = 100,
                  db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Device)
    if rack_id is not None:
        query = query.filter(Device.rack_id == rack_id)
    if status_filter:
        query = query.filter(Device.status == status_filter)
    if search:
        query = query.filter(Device.hostname.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/warranty-alerts", response_model=List[DeviceOut])
def warranty_alerts(days: int = 30, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role("Viewer"))):
    """Devices whose warranty expires within the given number of days."""
    cutoff = date.today() + timedelta(days=days)
    return db.query(Device).filter(Device.warranty_exp.isnot(None), Device.warranty_exp <= cutoff).all()


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=DeviceOut)
def create_device(payload: DeviceCreate, request: Request, db: Session = Depends(get_db),
                   current_user: User = Depends(require_role("Engineer"))):
    _check_u_space(db, payload.rack_id, payload.start_u, payload.height_u or 1)

    if payload.ip_address and db.query(Device).filter(Device.ip_address == payload.ip_address).first():
        raise HTTPException(status_code=400, detail="IP address already assigned to another device")

    device = Device(**payload.dict())
    db.add(device)
    db.commit()
    db.refresh(device)
    log_action(db, current_user.id, "device", "create", f"Created device {device.hostname}", request)
    return device


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, payload: DeviceUpdate, request: Request, db: Session = Depends(get_db),
                   current_user: User = Depends(require_role("Engineer"))):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    updates = payload.dict(exclude_unset=True)
    new_rack_id = updates.get("rack_id", device.rack_id)
    new_start_u = updates.get("start_u", device.start_u)
    new_height_u = updates.get("height_u", device.height_u)
    if "start_u" in updates or "height_u" in updates or "rack_id" in updates:
        _check_u_space(db, new_rack_id, new_start_u, new_height_u, exclude_device_id=device.id)

    for field, value in updates.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    log_action(db, current_user.id, "device", "update", f"Updated device {device.hostname}", request)
    return device


@router.post("/{device_id}/move", response_model=DeviceOut)
def move_device(device_id: int, payload: DeviceMove, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Engineer"))):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    _check_u_space(db, payload.rack_id, payload.start_u, device.height_u, exclude_device_id=device.id)
    old_rack_id = device.rack_id
    device.rack_id = payload.rack_id
    device.start_u = payload.start_u
    db.commit()
    db.refresh(device)
    log_action(db, current_user.id, "device", "move",
               f"Moved device {device.hostname} from rack {old_rack_id} to rack {payload.rack_id}", request)
    return device


@router.delete("/{device_id}")
def delete_device(device_id: int, request: Request, db: Session = Depends(get_db),
                   current_user: User = Depends(require_role("Admin"))):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Cables reference devices with a NOT NULL foreign key, so MySQL will
    # reject the delete outright if any cable still touches this device.
    # Block with a clear message instead of letting it crash as a 500 error.
    cable_count = db.query(Cable).filter(
        (Cable.source_device_id == device_id) | (Cable.dest_device_id == device_id)
    ).count()
    if cable_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete device: {cable_count} cable(s) are still connected to it. Remove those cables first.",
        )

    # Assets reference devices with a nullable foreign key, so detach them
    # instead of blocking the delete.
    db.query(Asset).filter(Asset.device_id == device_id).update({"device_id": None})

    hostname = device.hostname
    db.delete(device)
    db.commit()
    log_action(db, current_user.id, "device", "delete", f"Deleted device {hostname} (id {device_id})", request)
    return {"message": "Device deleted"}