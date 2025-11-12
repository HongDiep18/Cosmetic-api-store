# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from beanie import PydanticObjectId


class CategoryEmbeddedSchema(BaseModel):
    categoryId: str
    name: str


class BrandEmbeddedSchema(BaseModel):
    brandId: str
    name: str


class ProductBase(BaseModel):
    productName: str
    description: str
    price: float = Field(ge=0)
    originalPrice: Optional[float] = Field(default=None, ge=0)
    stock: int = Field(ge=0)
    status: str = Field(default="available")
    image: Optional[str] = None
    rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    reviewCount: Optional[int] = Field(default=0, ge=0)
    isFeatured: Optional[bool] = False
    isNew: Optional[bool] = False
    category: CategoryEmbeddedSchema
    brand: Optional[BrandEmbeddedSchema] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    productName: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    originalPrice: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = None
    image: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    reviewCount: Optional[int] = Field(default=None, ge=0)
    isFeatured: Optional[bool] = None
    isNew: Optional[bool] = None
    category: Optional[CategoryEmbeddedSchema] = None
    brand: Optional[BrandEmbeddedSchema] = None


class ProductOut(ProductBase):
    id: str = Field(alias="_id")
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class PaginatedResponse(BaseModel):
    data: list[ProductOut]
    total: int
    page: int
    limit: int
    totalPages: int


class StockUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=0, description="Số lượng tồn kho mới")
