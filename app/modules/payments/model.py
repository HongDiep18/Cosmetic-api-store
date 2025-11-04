from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
import uuid

from beanie import Document, PydanticObjectId
from pydantic import Field
from bson import ObjectId

# class Payment(Document):
#     PaymentID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
#     OrderID: str
#     PaymentMethod: str
#     Amount: float = Field(ge=0)
#     Status: Literal["Pending", "Paid", "Failed", "Refunded"] = "Pending"
#     PaymentDate: Optional[datetime] = None
#     CreatedAt: datetime = Field(default_factory=datetime.utcnow)
#     UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

#     class Settings:
#         name = "payments"

#     async def save(self, *args, **kwargs):  # type: ignore[override]
#         self.UpdatedAt = datetime.utcnow()
#         return await super().save(*args, **kwargs)



class Payment(Document):
    PaymentID:  Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    OrderID: Optional[PydanticObjectId]
    PaymentMethod: str
    Amount: float = Field(ge=0)
    Status: Literal["Pending", "Paid", "Failed", "Refunded"] = "Pending"
    PaymentDate: Optional[datetime] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payments"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
            PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
        }

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)