from __future__ import annotations
from datetime import datetime
import uuid

from beanie import Document, Indexed
from pydantic import Field


class Category(Document):
    CategoryID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    CategoryName: Indexed(str, unique=True)  # type: ignore[valid-type]
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "categories"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
