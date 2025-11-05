from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BrandBase(BaseModel):
    BrandName: str = Field(min_length=1)


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    BrandName: str | None = Field(default=None, min_length=1)


class BrandOut(BrandBase):
    id: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("id", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)


