from __future__ import annotations
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from bson import ObjectId
from typing import Optional

class Shipper(Document):
    ShipperID: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    AccountID: Optional[PydanticObjectId]
    FullName: str
    Phone: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "shippers"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            PydanticObjectId: str,
        }

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()  # Cập nhật UpdatedAt mỗi khi lưu tài liệu
        return await super().save(*args, **kwargs)
