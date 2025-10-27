# app/modules/admin_accountview/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class CustomerOut(BaseModel):
    CustomerID: str
    FullName: str
    Email: EmailStr
    Phone: Optional[str]
    Address: Optional[str]
    Status: str
    TotalOrders: Optional[int]
    CreatedAt: datetime

class ShipperOut(BaseModel):
    ShipperID: str
    FullName: str
    Email: EmailStr
    Phone: Optional[str]
    Status: str
    TotalDeliveries: Optional[int]
    CreatedAt: datetime
