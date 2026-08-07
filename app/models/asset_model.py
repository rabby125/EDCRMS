from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    assets = relationship("Asset", back_populates="category")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(100), unique=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(20), default="in_use")  # in_use, in_stock, retired

    category = relationship("AssetCategory", back_populates="assets")
    history = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")


class AssetHistory(Base):
    __tablename__ = "asset_history"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    action = Column(String(150), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset", back_populates="history")
