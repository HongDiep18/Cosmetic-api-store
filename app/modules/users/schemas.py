from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from beanie import Document, PydanticObjectId

class UserBase(BaseModel):
    AccountID: Optional[PydanticObjectId]
    FullName: str = Field(default="")
    Phone: Optional[str] = None
    Address: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    FullName: Optional[str] = None
    Phone: Optional[str] = None
    Address: Optional[str] = None


class UserOut(UserBase):
    UserID:  Optional[PydanticObjectId]
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("UserID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)


class UserWithEmailOut(UserOut):
    Email: str