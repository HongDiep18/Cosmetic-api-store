from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ShipperBase(BaseModel):
    # Use the same attribute names as the Beanie Document (fullName, phone)
    fullName: str = Field(min_length=1)
    phone: str = Field(min_length=1)


class ShipperCreate(ShipperBase):
    pass


class ShipperUpdate(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None


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
