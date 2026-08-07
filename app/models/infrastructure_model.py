from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    data_centers = relationship("DataCenter", back_populates="company", cascade="all, delete-orphan")


class DataCenter(Base):
    __tablename__ = "data_centers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="data_centers")
    buildings = relationship("Building", back_populates="data_center", cascade="all, delete-orphan")


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    data_center_id = Column(Integer, ForeignKey("data_centers.id"), nullable=False)
    name = Column(String(150), nullable=False)

    data_center = relationship("DataCenter", back_populates="buildings")
    floors = relationship("Floor", back_populates="building", cascade="all, delete-orphan")


class Floor(Base):
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    floor_number = Column(String(20), nullable=False)

    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False)
    room_name = Column(String(150), nullable=False)

    floor = relationship("Floor", back_populates="rooms")
    racks = relationship("Rack", back_populates="room", cascade="all, delete-orphan")


class Rack(Base):
    __tablename__ = "racks"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    rack_name = Column(String(150), nullable=False)
    rack_code = Column(String(50), unique=True, nullable=False)
    height_u = Column(Integer, default=42)  # 42U / 45U / 48U
    max_power_kw = Column(Numeric(6, 2), default=0)
    status = Column(String(20), default="active")

    room = relationship("Room", back_populates="racks")
    devices = relationship("Device", back_populates="rack", cascade="all, delete-orphan")

    def used_u(self) -> int:
        return sum(d.height_u for d in self.devices)

    def free_u(self) -> int:
        return self.height_u - self.used_u()
