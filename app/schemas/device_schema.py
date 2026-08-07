from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict


class _BaseModel(BaseModel):
    """Base with protected_namespaces disabled so fields like
    model_name / model_id don't trigger pydantic's 'model_' warning."""
    model_config = ConfigDict(protected_namespaces=())


class DeviceTypeCreate(BaseModel):
    name: str


class DeviceTypeOut(DeviceTypeCreate):
    id: int

    class Config:
        from_attributes = True


class VendorCreate(BaseModel):
    name: str


class VendorOut(VendorCreate):
    id: int

    class Config:
        from_attributes = True


class ManufacturerCreate(BaseModel):
    name: str


class ManufacturerOut(ManufacturerCreate):
    id: int

    class Config:
        from_attributes = True


class ModelCreate(_BaseModel):
    manufacturer_id: int
    model_name: str
    u_height: Optional[int] = 1
    power_watts: Optional[int] = 0


class ModelOut(ModelCreate):
    id: int

    class Config:
        from_attributes = True


class DeviceCreate(_BaseModel):
    rack_id: int
    device_type_id: Optional[int] = None
    vendor_id: Optional[int] = None
    model_id: Optional[int] = None
    hostname: str
    ip_address: Optional[str] = None
    mac: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None
    start_u: int
    height_u: Optional[int] = 1
    status: Optional[str] = "online"
    purchase_date: Optional[date] = None
    warranty_exp: Optional[date] = None


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac: Optional[str] = None
    serial: Optional[str] = None
    start_u: Optional[int] = None
    height_u: Optional[int] = None
    status: Optional[str] = None
    rack_id: Optional[int] = None
    warranty_exp: Optional[date] = None


class DeviceOut(DeviceCreate):
    id: int

    class Config:
        from_attributes = True


class DeviceMove(BaseModel):
    rack_id: int
    start_u: int