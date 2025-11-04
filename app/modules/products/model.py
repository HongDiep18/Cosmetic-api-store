from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import Field, field_validator
from bson import ObjectId


class Product(Document):
    ProductID: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ProductName: Indexed(str)  # type: ignore[valid-type]
    Description: str
    Price: float = Field(ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Active"
    Image: Optional[str] = None
    CategoryID: str
    CategoryName: Optional[str] = None  # Added for filtering
    
    @field_validator("CategoryID", mode="before")
    @classmethod
    def convert_category_id(cls, v):
        # Chuyển đổi ObjectId sang string
        if isinstance(v, ObjectId):
            return str(v)
        return v
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
