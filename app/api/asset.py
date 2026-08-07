from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.asset_model import Asset, AssetCategory, AssetHistory
from app.models.user_model import User
from app.schemas.asset_cable_schema import AssetCreate, AssetOut, AssetCategoryCreate, AssetCategoryOut
from app.core.permissions import require_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/assets", tags=["Asset"])
cat_router = APIRouter(prefix="/api/asset-categories", tags=["Asset Category"])


@cat_router.get("/", response_model=List[AssetCategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    return db.query(AssetCategory).all()


@cat_router.post("/", response_model=AssetCategoryOut)
def create_category(payload: AssetCategoryCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(require_role("Engineer"))):
    obj = AssetCategory(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[AssetOut])
def list_assets(category_id: Optional[int] = Query(None), status_filter: Optional[str] = Query(None, alias="status"),
                 search: Optional[str] = Query(None), db: Session = Depends(get_db),
                 current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Asset)
    if category_id is not None:
        query = query.filter(Asset.category_id == category_id)
    if status_filter:
        query = query.filter(Asset.status == status_filter)
    if search:
        query = query.filter(Asset.asset_tag.ilike(f"%{search}%"))
    return query.all()


@router.post("/", response_model=AssetOut)
def create_asset(payload: AssetCreate, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Engineer"))):
    if db.query(Asset).filter(Asset.asset_tag == payload.asset_tag).first():
        raise HTTPException(status_code=400, detail="Asset tag already exists")
    asset = Asset(**payload.dict())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    db.add(AssetHistory(asset_id=asset.id, action="Asset created"))
    db.commit()
    log_action(db, current_user.id, "asset", "create", f"Created asset {asset.asset_tag}", request)
    return asset


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: int, payload: AssetCreate, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Engineer"))):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in payload.dict().items():
        setattr(asset, field, value)
    db.add(AssetHistory(asset_id=asset.id, action="Asset updated"))
    db.commit()
    db.refresh(asset)
    log_action(db, current_user.id, "asset", "update", f"Updated asset {asset.asset_tag}", request)
    return asset


@router.get("/{asset_id}/history")
def asset_history(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    return db.query(AssetHistory).filter(AssetHistory.asset_id == asset_id).order_by(AssetHistory.date.desc()).all()


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, request: Request, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("Admin"))):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
    log_action(db, current_user.id, "asset", "delete", f"Deleted asset id {asset_id}", request)
    return {"message": "Asset deleted"}
