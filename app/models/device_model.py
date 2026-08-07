from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship

from app.database.connection import Base


class DeviceType(Base):
    __tablename__ = "device_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Server, Switch, Router, Firewall, UPS, Storage, PDU, Patch Panel

    devices = relationship("Device", back_populates="device_type")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Cisco, Dell, HP, Juniper, Fortinet, Huawei

    devices = relationship("Device", back_populates="vendor")


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    models = relationship("Model", back_populates="manufacturer")


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    model_name = Column(String(150), nullable=False)
    u_height = Column(Integer, default=1)
    power_watts = Column(Integer, default=0)

    manufacturer = relationship("Manufacturer", back_populates="models")
    devices = relationship("Device", back_populates="model")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    rack_id = Column(Integer, ForeignKey("racks.id"), nullable=False)
    device_type_id = Column(Integer, ForeignKey("device_types.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)

    hostname = Column(String(150), nullable=False)
    ip_address = Column(String(45), nullable=True)
    mac = Column(String(50), nullable=True)
    serial = Column(String(100), nullable=True)
    asset_tag = Column(String(100), nullable=True)

    start_u = Column(Integer, nullable=False)   # starting U position in rack
    height_u = Column(Integer, default=1)        # how many U it occupies

    status = Column(String(20), default="online")  # online, offline, alert
    purchase_date = Column(Date, nullable=True)
    warranty_exp = Column(Date, nullable=True)

    rack = relationship("Rack", back_populates="devices")
    device_type = relationship("DeviceType", back_populates="devices")
    vendor = relationship("Vendor", back_populates="devices")
    model = relationship("Model", back_populates="devices")
