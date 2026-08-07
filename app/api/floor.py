from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import Floor
from app.models.user_model import User
from app.schemas.infrastructure_schema import FloorCreate, FloorOut
from app.core.permissions import require_role
from app.utils.audit import log_action
from app.utils.cascade import collect_device_ids_under_rooms, detach_devices_before_delete

router = APIRouter(prefix="/api/floors", tags=["Floor"])


@router.get("/", response_model=List[FloorOut])
def list_floors(parent_id: Optional[int] = Query(None, description="Filter by building_id"),
               search: Optional[str] = Query(None), skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Floor)
    if parent_id is not None:
        query = query.filter(Floor.building_id == parent_id)
    if search:
        query = query.filter(Floor.floor_number.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=FloorOut)
def get_floor(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    obj = db.query(Floor).filter(Floor.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Floor not found")
    return obj


@router.post("/", response_model=FloorOut)
def create_floor(payload: FloorCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = Floor(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "floor", "create", f"Created floor id {obj.id}", request)
    return obj


@router.put("/{item_id}", response_model=FloorOut)
def update_floor(item_id: int, payload: FloorCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = db.query(Floor).filter(Floor.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Floor not found")
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "floor", "update", f"Updated floor id {item_id}", request)
    return obj


@router.delete("/{item_id}")
def delete_floor(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(Floor).filter(Floor.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Floor not found")

    device_ids = collect_device_ids_under_rooms(obj.rooms)
    detach_devices_before_delete(db, device_ids)

    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "floor", "delete", f"Deleted floor id {item_id}", request)
    return {"message": "Floor deleted"}