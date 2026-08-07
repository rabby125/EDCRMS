from typing import Optional
from pydantic import BaseModel


class AssetCategoryCreate(BaseModel):
    name: str


class AssetCategoryOut(AssetCategoryCreate):
    id: int

    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    asset_tag: str
    device_id: Optional[int] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = "in_use"


class AssetOut(AssetCreate):
    id: int

    class Config:
        from_attributes = True


class CableTypeCreate(BaseModel):
    name: str


class CableTypeOut(CableTypeCreate):
    id: int

    class Config:
        from_attributes = True


class CableCreate(BaseModel):
    cable_type_id: Optional[int] = None
    color: Optional[str] = None
    source_device_id: int
    source_port: Optional[str] = None
    dest_device_id: int
    dest_port: Optional[str] = None


class CableOut(CableCreate):
    id: int

    class Config:
        from_attributes = True
