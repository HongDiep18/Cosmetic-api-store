from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ShipperBase(BaseModel):
    fullName: str = Field(min_length=1)
    phone: str = Field(min_length=1)


class ShipperCreate(ShipperBase):
    pass


class ShipperUpdate(BaseModel):
    FullName: Optional[str] = None
    Phone: Optional[str] = None


class ShipperOut(ShipperBase):
    id: str = Field(alias="_id")
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_validator("id", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v) if v else None
