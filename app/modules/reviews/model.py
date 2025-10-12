from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from beanie import Document
from pydantic import Field


class Review(Document):
    ReviewID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    UserID: str
    ProductID: str
    Rating: int = Field(ge=1, le=5)
    Comment: Optional[str] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "reviews"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
