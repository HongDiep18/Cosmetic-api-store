from __future__ import annotations
from typing import Optional
from datetime import datetime
import uuid
from bson import ObjectId
from pydantic import Field
from beanie import Document, PydanticObjectId



class User(Document):
    UserID: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    AccountID: Optional[PydanticObjectId]
    FullName: str
    Phone: str
    Address: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            PydanticObjectId: str,
        }

    async def save(self, *args, **kwargs):  # type: ignore[override]
        # Cập nhật UpdatedAt trước khi lưu tài liệu
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)