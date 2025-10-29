# app/modules/admin_accountview/schemas.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional





class AccountOut(BaseModel):
    AccountID: str # hoặc _id nếu dùng 
    UserID: Optional[str]
    ShipperID: Optional[str]
    Email:str
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