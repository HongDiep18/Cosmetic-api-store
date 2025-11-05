from __future__ import annotations
from datetime import datetime
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field, ConfigDict
from bson import ObjectId


class Brand(Document):
    # Đồng bộ cấu trúc với Product/Category: dùng _id (PydanticObjectId)
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    BrandName: Indexed(str, unique=True)  # type: ignore[valid-type]
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "brands"

    # Cho phép encode ObjectId/PydanticObjectId về string trong JSON
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            PydanticObjectId: str,
        },
    )

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)


