from __future__ import annotations
from datetime import datetime
import uuid

from beanie import Document
from pydantic import Field


class Shipper(Document):
    ShipperID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    AccountID: str
    FullName: str
    Phone: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "shippers"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
