from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field


class Product(Document):
    ProductID: str  # = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    ProductName: Indexed(str)  # type: ignore[valid-type]
    Description: str
    Price: float = Field(ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Available"
    Image: Optional[str] = None
    CategoryID: str
    CategoryName: Optional[str] = None  # Added for filtering
    Brand: Optional[str] = None  # Added for filtering and display
    Rating: Optional[float] = Field(default=0.0, ge=0, le=5)  # Product rating
    ReviewCount: Optional[int] = Field(default=0, ge=0)  # Number of reviews
    IsFeatured: Optional[bool] = False  # Featured product flag
    IsNew: Optional[bool] = False  # New product flag
    OriginalPrice: Optional[float] = None  # Original price for discount display
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"
        use_revision = True

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
