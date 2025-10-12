from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    CategoryName: str = Field(min_length=1)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    CategoryName: Optional[str] = Field(default=None, min_length=1)


class CategoryOut(CategoryBase):
    CategoryID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("CategoryID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
