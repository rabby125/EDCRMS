from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import DataCenter
from app.models.user_model import User
from app.schemas.infrastructure_schema import DataCenterCreate, DataCenterOut
from app.core.permissions import require_role
from app.utils.audit import log_action
from app.utils.cascade import collect_device_ids_under_rooms, detach_devices_before_delete

router = APIRouter(prefix="/api/data-centers", tags=["DataCenter"])


@router.get("/", response_model=List[DataCenterOut])
def list_data_centers(parent_id: Optional[int] = Query(None, description="Filter by company_id"),
               search: Optional[str] = Query(None), skip: int = 0, limit: int = 100,
               db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(DataCenter)
    if parent_id is not None:
        query = query.filter(DataCenter.company_id == parent_id)
    if search:
        query = query.filter(DataCenter.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=DataCenterOut)
def get_data_center(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    obj = db.query(DataCenter).filter(DataCenter.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="DataCenter not found")
    return obj


@router.post("/", response_model=DataCenterOut)
def create_data_center(payload: DataCenterCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = DataCenter(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "datacenter", "create", f"Created datacenter id {obj.id}", request)
    return obj


@router.put("/{item_id}", response_model=DataCenterOut)
def update_data_center(item_id: int, payload: DataCenterCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    obj = db.query(DataCenter).filter(DataCenter.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="DataCenter not found")
    for field, value in payload.dict().items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "datacenter", "update", f"Updated datacenter id {item_id}", request)
    return obj


@router.delete("/{item_id}")
def delete_data_center(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(DataCenter).filter(DataCenter.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="DataCenter not found")

    rooms = [room for b in obj.buildings for fl in b.floors for room in fl.rooms]
    device_ids = collect_device_ids_under_rooms(rooms)
    detach_devices_before_delete(db, device_ids)

    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "datacenter", "delete", f"Deleted datacenter id {item_id}", request)
    return {"message": "DataCenter deleted"}