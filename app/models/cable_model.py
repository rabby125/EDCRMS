from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class CableType(Base):
    __tablename__ = "cable_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Cat6, Fiber Optic, DAC, Power Cable

    cables = relationship("Cable", back_populates="cable_type")


class Cable(Base):
    __tablename__ = "cables"

    id = Column(Integer, primary_key=True, index=True)
    cable_type_id = Column(Integer, ForeignKey("cable_types.id"), nullable=True)
    color = Column(String(30), nullable=True)

    source_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    source_port = Column(String(50), nullable=True)
    dest_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    dest_port = Column(String(50), nullable=True)

    cable_type = relationship("CableType", back_populates="cables")
    source_device = relationship("Device", foreign_keys=[source_device_id])
    dest_device = relationship("Device", foreign_keys=[dest_device_id])
