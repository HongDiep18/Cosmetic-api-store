from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
import uuid

from beanie import Document
from pydantic import Field


class Shipment(Document):
    ShipmentID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    OrderID: str
    ShipperID: str
    TrackingNumber: Optional[str] = None
    Status: Literal["Preparing", "In Transit", "Delivered", "Failed"] = "Preparing"
    ShipmentDate: Optional[datetime] = None
    EstimatedDeliveryDate: Optional[datetime] = None
    ActualDeliveryDate: Optional[datetime] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "shipments"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
