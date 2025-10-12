from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class ShipmentBase(BaseModel):
    OrderID: str
    ShipperID: str
    TrackingNumber: Optional[str] = None
    Status: Literal["Preparing", "In Transit", "Delivered", "Failed"] = "Preparing"
    ShipmentDate: Optional[datetime] = None
    EstimatedDeliveryDate: Optional[datetime] = None
    ActualDeliveryDate: Optional[datetime] = None


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    TrackingNumber: Optional[str] = None
    Status: Optional[Literal["Preparing", "In Transit", "Delivered", "Failed"]] = None
    ShipmentDate: Optional[datetime] = None
    EstimatedDeliveryDate: Optional[datetime] = None
    ActualDeliveryDate: Optional[datetime] = None


class ShipmentOut(ShipmentBase):
    ShipmentID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ShipmentID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
