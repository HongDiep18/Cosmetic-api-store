from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from beanie import PydanticObjectId
from enum import Enum


class ShipmentStatus(str, Enum):
    PREPARING = "Preparing"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    FAILED = "Failed"


class ShipmentBase(BaseModel):
    OrderID: str  # Accept string in API but convert to PydanticObjectId in handler
    ShipperID: str  # Accept string in API but convert to PydanticObjectId in handler
    TrackingNumber: Optional[str] = None
    Status: ShipmentStatus = ShipmentStatus.PREPARING
    ShipmentDate: Optional[datetime] = None
    EstimatedDeliveryDate: Optional[datetime] = None
    ActualDeliveryDate: Optional[datetime] = None

    class Config:
        json_encoders = {
            PydanticObjectId: str  # Convert ObjectId to string when returning response
        }


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    TrackingNumber: Optional[str] = None
    Status: Optional[ShipmentStatus] = None
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
    def cast_shipment_id(cls, v):
        return str(v)

    @field_validator("OrderID", "ShipperID", mode="before")
    @classmethod
    def cast_object_id_to_str(cls, v):
        return str(v)


class ShipmentStatsOut(BaseModel):
    TotalShipments: int
    Preparing: int
    Delivering: int
    Delivered: int

    class Config:
        from_attributes = True
