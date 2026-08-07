from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.cable_model import Cable, CableType
from app.models.user_model import User
from app.schemas.asset_cable_schema import CableCreate, CableOut, CableTypeCreate, CableTypeOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/cables", tags=["Cable"])
type_router = APIRouter(prefix="/api/cable-types", tags=["Cable Type"])


@type_router.get("/", response_model=List[CableTypeOut])
def list_cable_types(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    return db.query(CableType).all()


@type_router.post("/", response_model=CableTypeOut)
def create_cable_type(payload: CableTypeCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(require_role("Engineer"))):
    obj = CableType(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[CableOut])
def list_cables(device_id: Optional[int] = Query(None, description="Filter cables touching this device"),
                 db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Cable)
    if device_id is not None:
        query = query.filter((Cable.source_device_id == device_id) | (Cable.dest_device_id == device_id))
    return query.all()


@router.post("/", response_model=CableOut)
def create_cable(payload: CableCreate, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Engineer"))):
    if payload.source_device_id == payload.dest_device_id:
        raise HTTPException(status_code=400, detail="Source and destination device cannot be the same")
    cable = Cable(**payload.dict())
    db.add(cable)
    db.commit()
    db.refresh(cable)
    log_action(db, current_user.id, "cable", "create", f"Created cable id {cable.id}", request)
    return cable


@router.delete("/{cable_id}")
def delete_cable(cable_id: int, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Admin"))):
    cable = db.query(Cable).filter(Cable.id == cable_id).first()
    if not cable:
        raise HTTPException(status_code=404, detail="Cable not found")
    db.delete(cable)
    db.commit()
    log_action(db, current_user.id, "cable", "delete", f"Deleted cable id {cable_id}", request)
    return {"message": "Cable deleted"}
