# app/modules/admin_accountview/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional



class AccountViewOut(BaseModel):
    AccountID: str # hoặc _id nếu dùng 
    UserID: Optional[str]
    ShipperID: Optional[str]
    Email:EmailStr
    RoleName: Optional[str]
    RoleID: Optional[str]
    FullName: Optional[str]
    PasswordHash: Optional[str]
    Phone: Optional[str]
    Status: Optional[str]
    Address:Optional[str]
    TotalOrders: Optional[int]
    TotalDeliveries: Optional[int]
    CreatedAt: Optional[datetime]
    UpdatedAt: Optional[datetime]


