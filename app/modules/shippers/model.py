from __future__ import annotations
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from bson import ObjectId


class Shipper(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    fullName: str = Field(..., alias="FullName")
    phone: str = Field(..., alias="Phone")
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

        populate_by_name = True

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()  # Cập nhật UpdatedAt mỗi khi lưu tài liệu
        return await super().save(*args, **kwargs)
