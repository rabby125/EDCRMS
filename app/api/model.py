from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.device_model import Model as DeviceModel, Device
from app.models.user_model import User
from app.schemas.device_schema import ModelCreate, ModelOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/models", tags=["Model"])


@router.get("/", response_model=List[ModelOut])
def list_models(manufacturer_id: Optional[int] = Query(None), db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Viewer"))):
    query = db.query(DeviceModel)
    if manufacturer_id is not None:
        query = query.filter(DeviceModel.manufacturer_id == manufacturer_id)
    return query.all()


@router.post("/", response_model=ModelOut)
def create_model(payload: ModelCreate, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Engineer"))):
    obj = DeviceModel(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    log_action(db, current_user.id, "model", "create", f"Created model id {obj.id}", request)
    return obj


@router.delete("/{item_id}")
def delete_model(item_id: int, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Admin"))):
    obj = db.query(DeviceModel).filter(DeviceModel.id == item_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Model not found")
    db.query(Device).filter(Device.model_id == item_id).update({"model_id": None})
    db.delete(obj)
    db.commit()
    log_action(db, current_user.id, "model", "delete", f"Deleted model id {item_id}", request)
    return {"message": "Model deleted"}