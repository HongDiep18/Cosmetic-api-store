from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class CategoryBase(BaseModel):
    CategoryName: str = Field(min_length=1)
    Description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    CategoryName: Optional[str] = Field(default=None, min_length=1)
    Description: Optional[str] = None


class CategoryOut(CategoryBase):
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
