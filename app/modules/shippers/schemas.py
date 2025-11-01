from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from beanie import Document, PydanticObjectId

class ShipperBase(BaseModel):
    AccountID: Optional[PydanticObjectId]
    FullName: str = Field(min_length=1)
    Phone: str = Field(min_length=1)


class ShipperCreate(BaseModel):
    Email: EmailStr = Field(..., alias="Email")
    Password: str = Field(..., min_length=6, alias="Password")
    FullName: str = Field(..., alias="FullName")
    Phone: str | None = Field(default=None, alias="Phone")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

class ShipperUpdate(BaseModel):
    FullName: Optional[str] = None
    Phone: Optional[str] = None


class ShipperOut(ShipperBase):
    ShipperID:  Optional[PydanticObjectId]
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ShipperID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v) if v else None
