from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import Room
from app.models.user_model import User
from app.schemas.infrastructure_schema import RoomCreate, RoomOut
from app.core.permissions import require_role
from app.utils.audit import log_action
from app.utils.cascade import collect_device_ids_under_rooms, detach_devices_before_delete

router = APIRouter(prefix="/api/rooms", tags=["Room"])


@router.get("/", response_model=List[RoomOut])
def list_rooms(parent_id: Optional[int] = Query(None, description="Filter by floor_id"),
               search: Optional[str] = Query(None), skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Room)
    if parent_id is not None:
        query = query.filter(Room.floor_id == parent_id)
    if search:
        query = query.filter(Room.room_name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=RoomOut)
def get_room(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    obj = db.query(Room).filter(Room.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Room not found")
    return obj


@router.post("/", response_model=RoomOut)
def create_room(payload: RoomCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = Room(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "room", "create", f"Created room id {obj.id}", request)
    return obj


@router.put("/{item_id}", response_model=RoomOut)
def update_room(item_id: int, payload: RoomCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = db.query(Room).filter(Room.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Room not found")
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "room", "update", f"Updated room id {item_id}", request)
    return obj


@router.delete("/{item_id}")
def delete_room(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(Room).filter(Room.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Room not found")

    device_ids = collect_device_ids_under_rooms([obj])
    detach_devices_before_delete(db, device_ids)

    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "room", "delete", f"Deleted room id {item_id}", request)
    return {"message": "Room deleted"}