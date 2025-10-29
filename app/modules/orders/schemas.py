from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


# --- Các Schema Item (Sản phẩm trong đơn hàng) ---


class OrderItemBase(BaseModel):
    ProductID: str  # Will be converted to PydanticObjectId
    Quantity: int = Field(ge=1)
    Price: float = Field(ge=0)  # Giá tại thời điểm mua

    class Config:
        json_schema_extra = {
            "example": {
                "ProductID": "5f7d3a2e9d3e2a1234567890",
                "Quantity": 1,
                "Price": 29.99,
            }
        }


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemOut(OrderItemBase):
    class Config:
        from_attributes = True


# --- Các Schema Order (Đơn hàng) ---


class OrderBase(BaseModel):
    UserID: str  # Will be converted to PydanticObjectId
    ShippingAddress: str
    TotalAmount: float = Field(ge=0)
    Status: OrderStatus = OrderStatus.PENDING
    Items: List[OrderItemCreate] = []

    class Config:
        json_schema_extra = {
            "example": {
                "UserID": "7027bdf6-be3d-42a9-8ed3-9ecc8a41ca45",
                "ShippingAddress": "123 Street Name, City, Country",
                "TotalAmount": 59.98,
                "Status": "Pending",
                "Items": [
                    {
                        "ProductID": "5f7d3a2e9d3e2a1234567890",
                        "Quantity": 2,
                        "Price": 29.99,
                    }
                ],
            }
        }


class OrderCreate(BaseModel):
    ShippingAddress: str
    Items: List[OrderItemCreate]  # Array of items to be created

    class Config:
        json_schema_extra = {
            "example": {
                "ShippingAddress": "123 Đường ABC, Quận 1, TP. HCM",
                "Items": [
                    {
                        "ProductID": "67320b3afb12e61a29c18bb1",
                        "Quantity": 2,
                        "Price": 150000.0,
                    }
                ],
            }
        }


class OrderUpdate(BaseModel):
    ShippingAddress: Optional[str] = None
    Status: Optional[OrderStatus] = None


class OrderOut(OrderBase):
    id: str = Field(alias="_id")
    OrderDate: datetime
    Items: List[OrderItemOut]
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_validator("id", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v) if v else None
