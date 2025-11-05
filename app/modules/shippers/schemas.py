from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from beanie import PydanticObjectId


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
    ShipperID: Optional[PydanticObjectId]
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True

    @field_validator("ShipperID", mode="before")
    @classmethod
    def cast_id(cls, v):
        return str(v) if v else None


class OrderItemDetail(BaseModel):
    ProductID: str
    ProductName: str
    Quantity: int
    Price: float


class DeliverySummaryOut(BaseModel):
    """Schema for summarized delivery information shown in list view"""

    ShipmentID: str = Field(description="ID của vận đơn")
    TrackingNumber: str = Field(description="Mã vận đơn (VD: VD001-2024)")
    CustomerName: str = Field(description="Tên khách hàng")
    ShippingAddress: str = Field(description="Địa chỉ giao hàng")
    CODAmount: float = Field(description="Số tiền thu hộ (0 nếu đã thanh toán)")
    Status: str = Field(description="Trạng thái vận đơn")

    class Config:
        from_attributes = True


class DeliveryDetailsOut(BaseModel):
    # Shipment info
    TrackingNumber: str
    ShipmentStatus: str

    # Order info
    OrderID: str
    ShippingAddress: str
    TotalAmount: float
    OrderStatus: str

    # Customer info
    CustomerName: str
    CustomerPhone: str

    # Items
    Items: List[OrderItemDetail]

    # Payment info
    CODAmount: float = Field(
        description="Amount to collect (0 if paid online or already paid)"
    )
    PaymentMethod: str
    PaymentStatus: str

    class Config:
        from_attributes = True
