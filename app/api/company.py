from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.infrastructure_model import Company
from app.models.user_model import User
from app.schemas.infrastructure_schema import CompanyCreate, CompanyOut
from app.core.permissions import require_role
from app.utils.audit import log_action
from app.utils.cascade import collect_device_ids_under_rooms, detach_devices_before_delete

router = APIRouter(prefix="/api/companies", tags=["Company"])


@router.get("/", response_model=List[CompanyOut])
def list_companies(search: Optional[str] = Query(None), skip: int = 0, limit: int = 50,
                    db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    query = db.query(Company)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("Viewer"))):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyOut)
def create_company(payload: CompanyCreate, request: Request, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("Engineer"))):
    if db.query(Company).filter(Company.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Company code already exists")
    company = Company(**payload.dict())
    db.add(company)
    db.commit()
    db.refresh(company)
    log_action(db, current_user.id, "company", "create", f"Created company {company.name}", request)
    return company


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, payload: CompanyCreate, request: Request, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("Engineer"))):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in payload.dict().items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    log_action(db, current_user.id, "company", "update", f"Updated company {company.name}", request)
    return company


@router.delete("/{company_id}")
def delete_company(company_id: int, request: Request, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("Admin"))):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    rooms = [room for dc in company.data_centers for b in dc.buildings for fl in b.floors for room in fl.rooms]
    device_ids = collect_device_ids_under_rooms(rooms)
    detach_devices_before_delete(db, device_ids)

    db.delete(company)
    db.commit()
    log_action(db, current_user.id, "company", "delete", f"Deleted company id {company_id}", request)
    return {"message": "Company deleted"}