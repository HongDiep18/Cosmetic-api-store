# app/modules/admin_accountview/controller.py
from app.modules.auth.model import Account
from app.modules.users.model import User
from app.modules.shippers.model import Shipper
from app.modules.shipments.model import Shipment

from app.modules.admin_accountview.schemas import CustomerOut, ShipperOut
from app.modules.orders.model import Order

from beanie.operators import In

# ------------------- CUSTOMER -------------------
async def get_all_customers():
    users = await User.find_all().to_list()
    print("===> Users found:",users)
    account_ids = [u.AccountID for u in users if u.AccountID]

    accounts = await Account.find_many(In(Account.id, account_ids)).to_list()

    results = []
    for user in users:
        acc = next((a for a in accounts if str(a.id) == str(user.AccountID)), None)
        results.append(
            CustomerOut(
                CustomerID=str(user.id),
                FullName=user.FullName,
                Email=acc.Email if acc else "",
                Phone=user.Phone,
                Address=user.Address,
                Status=acc.Status if acc else "Unknown",
                TotalOrders= await count_orders_by_user(user.id),
                CreatedAt=user.CreatedAt,
            )
        )
    return results

"""Đếm số đơn hàng của 1 khách hàng"""
async def count_orders_by_user(user_id):
    return await Order.find(Order.UserID == user_id).count()


# ------------------- SHIPPER -------------------
async def get_all_shippers():
    shippers = await Shipper.find_all().to_list()
    print("===> shippers found:",shippers)
    account_ids = [s.AccountID for s in shippers if s.AccountID]

    accounts = await Account.find_many(In(Account.id, account_ids)).to_list()

    results = []
    for s in shippers:
        acc = next((a for a in accounts if str(a.id) == str(s.AccountID)), None)
        results.append(
            ShipperOut(
                ShipperID=str(s.id),
                FullName=s.FullName,
                Email=acc.Email if acc else "",
                Phone=s.Phone,
                Status=acc.Status if acc else "Unknown",
                TotalDeliveries= await count_orders_by_shipper(s.id),
                CreatedAt=s.CreatedAt,
            )
        )
    return results

async def count_orders_by_shipper(shipper_id):
    return await Shipment.find({"ShipperID" : shipper_id}).count()

