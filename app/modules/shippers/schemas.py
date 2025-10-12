from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ShipperBase(BaseModel):
    AccountID: str
    FullName: str = Field(min_length=1)
    Phone: str = Field(min_length=1)


class ShipperCreate(ShipperBase):
    pass


class ShipperUpdate(BaseModel):
    FullName: Optional[str] = None
    Phone: Optional[str] = None


class ShipperOut(ShipperBase):
    ShipperID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ShipperID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
