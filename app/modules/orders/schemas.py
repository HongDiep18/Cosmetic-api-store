from __future__ import annotations
from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class OrderItemBase(BaseModel):
    ProductID: str
    Quantity: int = Field(ge=1)
    Price: float = Field(ge=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemOut(OrderItemBase):
    OrderID: str

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    UserID: str
    ShippingAddress: str
    TotalAmount: float = Field(ge=0)
    Status: Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"] = (
        "Pending"
    )


class OrderCreate(BaseModel):
    ShippingAddress: str
    Items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    ShippingAddress: Optional[str] = None
    Status: Optional[
        Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
    ] = None


class OrderOut(OrderBase):
    OrderID: str
    OrderDate: datetime
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("OrderID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v)
