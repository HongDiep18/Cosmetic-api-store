from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from bson import ObjectId

class StatusPayment(Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refund"


class PaymentBase(BaseModel):
    OrderID: str
    PaymentMethod: str
    Amount: float = Field(ge=0)
    
    Status: StatusPayment = StatusPayment.PENDING
    PaymentDate: Optional[datetime] = Field(default_factory=datetime.utcnow)


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    Status: Optional[StatusPayment] = None
    PaymentDate: Optional[datetime] = None


class PaymentOut(PaymentBase):
    PaymentID: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


    @field_validator("PaymentID", mode="before")
    @classmethod
    def cast_payment_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_validator("OrderID", mode="before")
    @classmethod
    def cast_order_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
