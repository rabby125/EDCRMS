from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    code: str
    status: Optional[str] = "active"


class CompanyOut(CompanyCreate):
    id: int

    class Config:
        from_attributes = True


class DataCenterCreate(BaseModel):
    company_id: int
    name: str
    location: Optional[str] = None


class DataCenterOut(DataCenterCreate):
    id: int

    class Config:
        from_attributes = True


class BuildingCreate(BaseModel):
    data_center_id: int
    name: str


class BuildingOut(BuildingCreate):
    id: int

    class Config:
        from_attributes = True


class FloorCreate(BaseModel):
    building_id: int
    floor_number: str


class FloorOut(FloorCreate):
    id: int

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    floor_id: int
    room_name: str


class RoomOut(RoomCreate):
    id: int

    class Config:
        from_attributes = True


class RackCreate(BaseModel):
    room_id: int
    rack_name: str
    rack_code: str
    height_u: Optional[int] = 42
    max_power_kw: Optional[Decimal] = 0
    status: Optional[str] = "active"


class RackOut(RackCreate):
    id: int
    used_u: Optional[int] = 0
    free_u: Optional[int] = 0

    class Config:
        from_attributes = True


class RackUpdate(BaseModel):
    rack_name: Optional[str] = None
    height_u: Optional[int] = None
    max_power_kw: Optional[Decimal] = None
    status: Optional[str] = None
