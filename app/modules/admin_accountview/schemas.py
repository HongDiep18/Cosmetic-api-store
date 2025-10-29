# # app/modules/admin_accountview/schemas.py
# from datetime import datetime
# from pydantic import BaseModel
# from typing import Optional


# class CustomerOut(BaseModel):
#     CustomerID: str
#     FullName: str
#     Email: Optional[str] = ""
#     Phone: Optional[str] = None
#     Address: Optional[str] = None
#     Status: str
#     TotalOrders: int = 0
#     CreatedAt: datetime

#     class Config:
#         from_attributes = True


# class ShipperOut(BaseModel):
#     ShipperID: str
#     FullName: str
#     Email: Optional[str] = ""
#     Phone: Optional[str] = None
#     Status: str
#     TotalDeliveries: int = 0
#     CreatedAt: datetime

#     class Config:
#         from_attributes = True
