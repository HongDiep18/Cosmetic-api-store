from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
import uuid

from beanie import Document
from pydantic import Field
from bson import ObjectId
from beanie import Document, PydanticObjectId

class Shipment(Document):
    ShipmentID: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    OrderID: Optional[PydanticObjectId]
    ShipperID: Optional[PydanticObjectId]
    TrackingNumber: Optional[str] = None
    Status: Literal["Preparing", "In Transit", "Delivered", "Failed"] = "Preparing"
    ShipmentDate: Optional[datetime] = None
    EstimatedDeliveryDate: Optional[datetime] = None
    ActualDeliveryDate: Optional[datetime] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "shipments"
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
            PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
        }
    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
