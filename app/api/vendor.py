from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.device_model import Vendor, Device
from app.models.user_model import User
from app.schemas.device_schema import VendorCreate, VendorOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/vendors", tags=["Vendor"])


@router.get("/", response_model=List[VendorOut])
def list_vendors(search: Optional[str] = Query(None), db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Vendor)
    if search:
        query = query.filter(Vendor.name.ilike(f"%{search}%"))
    return query.all()


@router.post("/", response_model=VendorOut)
def create_vendor(payload: VendorCreate, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Engineer"))):
    if db.query(Vendor).filter(Vendor.name == getattr(payload, "name")).first():
        raise HTTPException(status_code=400, detail="Vendor already exists")
    obj = Vendor(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "vendor", "create", f"Created vendor id {obj.id}", request)
    return obj


@router.delete("/{item_id}")
def delete_vendor(item_id: int, request: Request, db: Session = Depends(get_db),
               current_user: User = Depends(require_role("Admin"))):
    obj = db.query(Vendor).filter(Vendor.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.query(Device).filter(Device.vendor_id == item_id).update({"vendor_id": None})
    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "vendor", "delete", f"Deleted vendor id {item_id}", request)
    return {"message": "Vendor deleted"}