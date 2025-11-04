from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class ProductBase(BaseModel):
    ProductName: str
    Brand: Optional[str] = None
    Description: str
    Price: float = Field(ge=0)
    OriginalPrice: Optional[float] = Field(default=None, ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Active"
    Image: Optional[str] = None
    CategoryID: str
    CategoryName: Optional[str] = None
    
    @field_validator("CategoryID", mode="before")
    @classmethod
    def convert_category_id(cls, v):
        # Chuyển đổi ObjectId sang string nếu cần
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    Rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    ReviewCount: Optional[int] = Field(default=0, ge=0)
    IsFeatured: Optional[bool] = False
    IsNew: Optional[bool] = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    ProductName: Optional[str] = None
    Brand: Optional[str] = None
    Description: Optional[str] = None
    Price: Optional[float] = Field(default=None, ge=0)
    OriginalPrice: Optional[float] = Field(default=None, ge=0)
    Stock: Optional[int] = Field(default=None, ge=0)
    Status: Optional[str] = None
    Image: Optional[str] = None
    CategoryID: Optional[str] = None
    CategoryName: Optional[str] = None
    Rating: Optional[float] = Field(default=None, ge=0, le=5)
    ReviewCount: Optional[int] = Field(default=None, ge=0)
    IsFeatured: Optional[bool] = None
    IsNew: Optional[bool] = None


class ProductOut(ProductBase):
    id: str = Field(alias="_id")
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_validator("id", mode="before")
    @classmethod
    def cast_id(cls, v):
        if v is None:
            raise ValueError("id is None")
        return str(v)


class PaginatedResponse(BaseModel):
    data: list[ProductOut]
    total: int
    page: int
    limit: int
    totalPages: int


class StockUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=0, description="Số lượng tồn kho mới")