from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import Building
from app.models.user_model import User
from app.schemas.infrastructure_schema import BuildingCreate, BuildingOut
from app.core.permissions import require_role
from app.utils.audit import log_action
from app.utils.cascade import collect_device_ids_under_rooms, detach_devices_before_delete

router = APIRouter(prefix="/api/buildings", tags=["Building"])


@router.get("/", response_model=List[BuildingOut])
def list_buildings(parent_id: Optional[int] = Query(None, description="Filter by data_center_id"),
               search: Optional[str] = Query(None), skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Building)
    if parent_id is not None:
        query = query.filter(Building.data_center_id == parent_id)
    if search:
        query = query.filter(Building.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=BuildingOut)
def get_building(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    obj = db.query(Building).filter(Building.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Building not found")
    return obj


@router.post("/", response_model=BuildingOut)
def create_building(payload: BuildingCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = Building(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "building", "create", f"Created building id {obj.id}", request)
    return obj


@router.put("/{item_id}", response_model=BuildingOut)
def update_building(item_id: int, payload: BuildingCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = db.query(Building).filter(Building.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Building not found")
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "building", "update", f"Updated building id {item_id}", request)
    return obj


@router.delete("/{item_id}")
def delete_building(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(Building).filter(Building.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Building not found")

    rooms = [room for fl in obj.floors for room in fl.rooms]
    device_ids = collect_device_ids_under_rooms(rooms)
    detach_devices_before_delete(db, device_ids)

    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "building", "delete", f"Deleted building id {item_id}", request)
    return {"message": "Building deleted"}