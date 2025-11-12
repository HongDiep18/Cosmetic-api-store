# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class CategoryEmbedded(BaseModel):
    categoryId: PydanticObjectId
    name: str


class BrandEmbedded(BaseModel):
    brandId: PydanticObjectId
    name: str


class Product(Document):
    productName: Indexed(str)  # type: ignore[valid-type]
    description: str
    price: float = Field(ge=0)
    originalPrice: Optional[float] = None
    stock: int = Field(ge=0)
    status: str = Field(default="available")  # available, low_stock, out_of_stock
    image: Optional[str] = None
    rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    reviewCount: Optional[int] = Field(default=0, ge=0)
    isFeatured: Optional[bool] = False
    isNew: Optional[bool] = False
    category: CategoryEmbedded
    brand: BrandEmbedded
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"
        use_revision = False

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            PydanticObjectId: str,
        },
    )

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.updatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
