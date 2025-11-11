from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class OrderItemBase(BaseModel):
    ProductID: str  # Will be converted to PydanticObjectId
    Quantity: int = Field(ge=1)
    Price: float = Field(ge=0)  # Giá tại thời điểm mua

    @field_validator("ProductID", mode="before")
    @classmethod
    def convert_product_id(cls, v):
        """Convert ObjectId to string"""
        if isinstance(v, (ObjectId, str)):
            return str(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ProductID": "5f7d3a2e9d3e2a1234567890",
                "Quantity": 1,
                "Price": 29.99,
            }
        }


class OrderItemCreate(OrderItemBase):
    # ProductName: str
    pass


class OrderItemOut(OrderItemBase):
    @field_validator("ProductID", mode="before")
    @classmethod
    def cast_product_id(cls, v):
        """Accept ObjectId or string and return a plain string id"""
        # Handle ObjectId from bson
        if isinstance(v, ObjectId):
            return str(v)
        # Handle string
        if isinstance(v, str):
            return v
        # Try to convert anything else
        try:
            return str(v) if v is not None else v
        except Exception:
            return v

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


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status only"""

    Status: OrderStatus = Field(..., description="New status for the order")

    @field_validator("Status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        """Normalize status by stripping whitespace and finding matching enum value"""
        if isinstance(v, str):
            # Strip whitespace
            v = v.strip()
            # Try to find matching enum value (case-insensitive)
            for status in OrderStatus:
                if status.value.lower() == v.lower():
                    return status
            # If exact match not found, try direct match
            try:
                return OrderStatus(v)
            except ValueError:
                # If still not found, return original to trigger validation error
                return v
        return v

    class Config:
        json_schema_extra = {"example": {"Status": "Confirmed"}}


class OrderOut(OrderBase):
    id: str = Field(alias="_id")
    OrderDate: datetime
    Items: List[OrderItemOut]
    CreatedAt: datetime
    UpdatedAt: datetime

    @field_validator("Items", mode="before")
    @classmethod
    def normalize_items(cls, v):
        """Normalize Items to ensure ProductID is converted from ObjectId to string"""
        if isinstance(v, list):
            normalized_items = []
            for item in v:
                if isinstance(item, dict):
                    # Convert ObjectId to string
                    if "ProductID" in item:
                        pid = item["ProductID"]
                        if isinstance(pid, ObjectId):
                            item = {**item, "ProductID": str(pid)}
                    normalized_items.append(item)
                elif hasattr(item, "ProductID"):
                    # Handle object with ProductID attribute
                    if isinstance(item.ProductID, ObjectId):
                        item.ProductID = str(item.ProductID)
                    normalized_items.append(item)
                else:
                    normalized_items.append(item)
            return normalized_items
        return v

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_validator("id", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v) if v else None

    @field_validator("UserID", mode="before")
    @classmethod
    def cast_user_id(cls, v):
        try:
            return str(v) if v is not None else v
        except Exception:
            return v

class OrderOutCustom(OrderOut):
    PaymentID: Optional[str]
    PaymentMethod: Optional[str]