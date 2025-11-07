from __future__ import annotations
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from bson import ObjectId
from .schemas import OrderStatus

from typing import Optional, Any


# class OrderItem(BaseModel):
#     ProductID: str
#     Quantity: int = Field(ge=1)
#     Price: float = Field(ge=0)


# class Order(Document):
#     id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
#     UserID: str
#     ShippingAddress: str
#     OrderDate: datetime = Field(default_factory=datetime.utcnow)
#     TotalAmount: float = Field(ge=0)
#     Status: OrderStatus = OrderStatus.PENDING
#     Items: list[OrderItem] = []  # Array of embedded items
#     CreatedAt: datetime = Field(default_factory=datetime.utcnow)
#     UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

#     def __init__(self, **data):
#         super().__init__(**data)
#         # Ensure _id is always converted to string in the output
#         if hasattr(self, "_id"):
#             self._id = str(self._id)

#     class Settings:
#         name = "orders"

#     class Config:
#         arbitrary_types_allowed = True
#         json_encoders = {
#             ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
#             PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
#         }

#     async def save(self, *args, **kwargs):  # type: ignore[override]
#         self.UpdatedAt = datetime.utcnow()
#         return await super().save(*args, **kwargs)



class OrderItem(BaseModel):

    # Allow both string and ObjectId-like values (from older data)
    ProductID: Optional[PydanticObjectId]
    Quantity: int = Field(ge=1)
    Price: float = Field(ge=0)
    
    model_config = {
        "json_encoders": {
            ObjectId: str,
            PydanticObjectId: str  # Khi serialize ra JSON, ObjectId → string
        }
    }
    
class Order(Document):
    OrderID: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    UserID: Optional[PydanticObjectId]
    ShippingAddress: str
    OrderDate: datetime = Field(default_factory=datetime.utcnow)
    TotalAmount: float = Field(ge=0)
    Status: OrderStatus = OrderStatus.PENDING
    Items: list[OrderItem] = []  # Array of embedded items
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    # def __init__(self, **data):
    #     super().__init__(**data)
    #     # Ensure _id is always converted to string in the output
    #     if hasattr(self, "_id"):
    #         self._id = str(self._id)

    class Settings:
        name = "orders"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
            PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
        }

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)