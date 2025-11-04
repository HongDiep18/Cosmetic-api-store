from __future__ import annotations
from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field, ConfigDict
from bson import ObjectId


class Category(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    # CatgoryId: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    CategoryName: Indexed(str, unique=True)  # type: ignore[valid-type]
    Description: Optional[str] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure _id is always converted to string in the output
        if hasattr(self, "_id"):
            self._id = str(self._id)

    class Settings:
        name = "categories"

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
