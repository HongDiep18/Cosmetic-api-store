# app/modules/admin_accountview/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class ProfileOut(BaseModel):
    fullName: str
    phone: str
    address: Optional[str] = None


class AccountViewOut(BaseModel):
    _id: str  # AccountID
    email: EmailStr
    role: str  # RoleName
    status: str
    profile: ProfileOut
    passwordResetToken: Optional[str] = None
    passwordResetExpires: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    TotalOrders: Optional[int] = 0
    TotalDeliveries: Optional[int] = 0
