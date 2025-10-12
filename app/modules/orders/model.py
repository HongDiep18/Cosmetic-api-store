from __future__ import annotations
from typing import Literal
from datetime import datetime
import uuid

from beanie import Document
from pydantic import Field


class Order(Document):
    OrderID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    UserID: str
    ShippingAddress: str
    OrderDate: datetime = Field(default_factory=datetime.utcnow)
    TotalAmount: float = Field(ge=0)
    Status: Literal["Pending", "Processing", "Shipped", "Delivered", "Cancelled"] = (
        "Pending"
    )
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)


class OrderItem(Document):
    OrderID: str
    ProductID: str
    Quantity: int = Field(ge=1)
    Price: float = Field(ge=0)

    class Settings:
        name = "order_items"
        indexes = [
            [("OrderID", 1), ("ProductID", 1)],  # Compound primary key
        ]
