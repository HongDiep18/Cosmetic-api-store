from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ReviewBase(BaseModel):
    UserID: str
    ProductID: str
    Rating: int = Field(ge=1, le=5)
    Comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    Rating: Optional[int] = Field(default=None, ge=1, le=5)
    Comment: Optional[str] = None


class ReviewOut(ReviewBase):
    ReviewID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ReviewID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
