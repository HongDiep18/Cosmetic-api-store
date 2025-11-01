from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
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
    ProductID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def ensure_product_id(cls, data):
        if isinstance(data, dict):
            if not data.get("ProductID") and data.get("id"):
                data["ProductID"] = str(data["id"])
            return data
        if hasattr(data, 'model_dump'):
            data_dict = data.model_dump()
            if not data_dict.get("ProductID"):
                if hasattr(data, 'id') and data.id:
                    data_dict["ProductID"] = str(data.id)
                elif hasattr(data, '_id') and data._id:
                    data_dict["ProductID"] = str(data._id)
            return data_dict
        if hasattr(data, 'ProductID'):
            return data
        if hasattr(data, 'id') and data.id:
            result = {}
            if hasattr(data, '__dict__'):
                result.update(data.__dict__)
            result["ProductID"] = str(data.id)
            return result
        
        return data
    
    @field_validator("ProductID", mode="before")
    @classmethod
    def cast_id(cls, v):
        if v is None:
            raise ValueError("ProductID is None")
        return str(v)


class PaginatedResponse(BaseModel):
    data: list[ProductOut]
    total: int
    page: int
    limit: int
    totalPages: int