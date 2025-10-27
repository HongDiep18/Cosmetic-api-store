from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    ProductName: str
    Description: str
    Price: float = Field(ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Available"
    Image: Optional[str] = None
    CategoryID: str
    CategoryName: Optional[str] = None
    Brand: Optional[str] = None
    Rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    ReviewCount: Optional[int] = Field(default=0, ge=0)
    IsFeatured: Optional[bool] = False
    IsNew: Optional[bool] = False
    OriginalPrice: Optional[float] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    ProductName: Optional[str] = None
    Description: Optional[str] = None
    Price: Optional[float] = Field(default=None, ge=0)
    Stock: Optional[int] = Field(default=None, ge=0)
    Status: Optional[str] = None
    Image: Optional[str] = None
    CategoryID: Optional[str] = None
    CategoryName: Optional[str] = None
    Brand: Optional[str] = None
    Rating: Optional[float] = Field(default=None, ge=0, le=5)
    ReviewCount: Optional[int] = Field(default=None, ge=0)
    IsFeatured: Optional[bool] = None
    IsNew: Optional[bool] = None
    OriginalPrice: Optional[float] = None


class ProductOut(ProductBase):
    ProductID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ProductID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
