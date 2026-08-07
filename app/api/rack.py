from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import Rack
from app.models.device_model import Device
from app.models.user_model import User
from app.schemas.infrastructure_schema import RackCreate, RackOut, RackUpdate
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/racks", tags=["Rack"])


def _to_out(rack: Rack) -> dict:
    return {
        "id": rack.id,
        "room_id": rack.room_id,
        "rack_name": rack.rack_name,
        "rack_code": rack.rack_code,
        "height_u": rack.height_u,
        "max_power_kw": rack.max_power_kw,
        "status": rack.status,
        "used_u": rack.used_u(),
        "free_u": rack.free_u(),
    }


@router.get("/", response_model=List[RackOut])
def list_racks(room_id: Optional[int] = Query(None), search: Optional[str] = Query(None),
               skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Rack)
    if room_id is not None:
        query = query.filter(Rack.room_id == room_id)
    if search:
        query = query.filter(Rack.rack_name.ilike(f"%{search}%"))
    racks = query.offset(skip).limit(limit).all()
    return [_to_out(r) for r in racks]


@router.get("/{rack_id}", response_model=RackOut)
def get_rack(rack_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    return _to_out(rack)


@router.get("/{rack_id}/layout")
def rack_layout(rack_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    """Returns a U-by-U visual map of the rack: which U slots are occupied by which device."""
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")

    slots = {u: None for u in range(1, rack.height_u + 1)}
    for device in rack.devices:
        for u in range(device.start_u, device.start_u + device.height_u):
            if 1 <= u <= rack.height_u:
                slots[u] = {"device_id": device.id, "hostname": device.hostname, "status": device.status}

    return {
        "rack_id": rack.id,
        "rack_name": rack.rack_name,
        "height_u": rack.height_u,
        "used_u": rack.used_u(),
        "free_u": rack.free_u(),
        "slots": slots,
    }


@router.post("/", response_model=RackOut)
def create_rack(payload: RackCreate, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Engineer"))):
    if db.query(Rack).filter(Rack.rack_code == payload.rack_code).first():
        raise HTTPException(status_code=400, detail="Rack code already exists")
    rack = Rack(**payload.dict())
    db.add(rack)
    db.commit()
    db.refresh(rack)
    log_action(db, current_user.id, "rack", "create", f"Created rack {rack.rack_name}", request)
    return _to_out(rack)


@router.put("/{rack_id}", response_model=RackOut)
def update_rack(rack_id: int, payload: RackUpdate, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Engineer"))):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(rack, field, value)
    db.commit()
    db.refresh(rack)
    log_action(db, current_user.id, "rack", "update", f"Updated rack {rack.rack_name}", request)
    return _to_out(rack)


@router.delete("/{rack_id}")
def delete_rack(rack_id: int, request: Request, db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Admin"))):
    rack = db.query(Rack).filter(Rack.id == rack_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    if rack.devices:
        raise HTTPException(status_code=400, detail="Cannot delete rack with devices still mounted")
    db.delete(rack)
    db.commit()
    log_action(db, current_user.id, "rack", "delete", f"Deleted rack id {rack_id}", request)
    return {"message": "Rack deleted"}
