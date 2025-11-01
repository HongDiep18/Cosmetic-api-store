# app/modules/admin_accountview/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional



class AccountOut(BaseModel):
    AccountID: str # hoặc _id nếu dùng 
    UserID: Optional[str]
    ShipperID: Optional[str]
    Email:EmailStr
    RoleName: Optional[str]
    RoleID: Optional[str]
    FullName: str
    PasswordHash: str
    Phone: str
    Status: str
    Address:Optional[str]
    TotalOrders: Optional[int]
    TotalDeliveries: Optional[int]
    CreatedAt: Optional[datetime]
    UpdatedAt: Optional[datetime]


# class AccountUpdateOut(BaseModel):
#     AccountID: str
#     UserID: Optional[str]
#     ShipperID: Optional[str]
#     FullName: Optional[str]
#     Phone: Optional[str]
#     Status: Optional[str]
#     Address: Optional[str]
