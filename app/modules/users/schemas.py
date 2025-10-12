from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    AccountID: str
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
    UserID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("UserID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
