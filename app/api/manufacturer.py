from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.device_model import Manufacturer, Model as DeviceModel
from app.models.user_model import User
from app.schemas.device_schema import ManufacturerCreate, ManufacturerOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/manufacturers", tags=["Manufacturer"])


@router.get("/", response_model=List[ManufacturerOut])
def list_manufacturers(search: Optional[str] = Query(None), db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Manufacturer)
    if search:
        query = query.filter(Manufacturer.name.ilike(f"%{search}%"))
    return query.all()


@router.post("/", response_model=ManufacturerOut)
def create_manufacturer(payload: ManufacturerCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    if db.query(Manufacturer).filter(Manufacturer.name == getattr(payload, "name")).first():
        raise HTTPException(status_code=400, detail="Manufacturer already exists")
    obj = Manufacturer(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "manufacturer", "create", f"Created manufacturer id {obj.id}", request)
    return obj


@router.delete("/{item_id}")
def delete_manufacturer(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(Manufacturer).filter(Manufacturer.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    model_count = db.query(DeviceModel).filter(DeviceModel.manufacturer_id == item_id).count()
    if model_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete manufacturer: {model_count} model(s) still belong to it. Delete or reassign those models first.",
        )
    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "manufacturer", "delete", f"Deleted manufacturer id {item_id}", request)
    return {"message": "Manufacturer deleted"}