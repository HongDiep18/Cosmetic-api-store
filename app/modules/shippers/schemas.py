from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
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


class ShipperOut(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    role: str
    status: str
    profile: dict  # Profile with fullName, phone
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both 'id' and '_id' for input


class OrderItemDetail(BaseModel):
    ProductID: str
    ProductName: str
    Quantity: int
    Price: float


class DeliverySummaryOut(BaseModel):
    """Schema for summarized delivery information shown in list view"""

    ShipmentID: str = Field(description="ID của vận đơn")
    OrderID: str = Field(description="ID của đơn hàng (để cập nhật trạng thái)")
    TrackingNumber: str = Field(description="Mã vận đơn (VD: VD001-2024)")
    CustomerName: str = Field(description="Tên khách hàng")
    ShippingAddress: str = Field(description="Địa chỉ giao hàng")
    CODAmount: float = Field(description="Số tiền thu hộ (0 nếu đã thanh toán)")
    Status: str = Field(description="Trạng thái vận đơn/đơn hàng")
    CustomerPhone: Optional[str] = Field(
        default="", description="Số điện thoại khách hàng"
    )
    Items: Optional[List[OrderItemDetail]] = Field(
        default=[], description="Danh sách sản phẩm"
    )

    class Config:
        from_attributes = True


class DeliveryStatusUpdate(BaseModel):
    """Schema for updating delivery/order status from shipper portal"""

    status: str = Field(
        ...,
        description="New status for the order (e.g., 'Shipped', 'Delivered', 'Failed')",
    )

    class Config:
        json_schema_extra = {"example": {"status": "Shipped"}}


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
