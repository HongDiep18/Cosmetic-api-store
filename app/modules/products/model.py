from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


class Product(Document):
    ProductID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    ProductName: Indexed(str)  # type: ignore[valid-type]
    Description: str
    Price: float = Field(ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Available"
    Image: Optional[str] = None
    CategoryID: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"
        use_revision = True

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
