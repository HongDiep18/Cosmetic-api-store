# app/modules/admin_accountview/controller.py
from app.modules.auth.model import Account
from app.modules.users.model import User
from app.modules.shippers.model import Shipper
from app.modules.shipments.model import Shipment
from app.modules.auth.model import Role

from app.modules.account.schemas import  AccountViewOut
from app.modules.orders.model import Order



# ------------------- ACCOUNT VIEW -------------------
async def get_account_custom():
    shippers = await Shipper.find_all().to_list()
    accounts = await Account.find_all().to_list()
    users = await User.find_all().to_list()
    roles = await Role.find_all().to_list()

    results = []

    for acc in accounts:
        # Tìm RoleName tương ứng
        role = next((r for r in roles if str(r.id) == str(acc.RoleID)), None)
        role_name = role.RoleName if role else None

        user = None
        shipper = None

        # Nếu là User → tìm trong bảng users
        if role_name == "User":
            user = next((u for u in users if str(u.AccountID) == str(acc.id)), None)

        # Nếu là Shipper → tìm trong bảng shippers
        elif role_name == "Shipper":
            shipper = next((s for s in shippers if str(s.AccountID) == str(acc.id)), None)

        # Lấy thống kê tương ứng
        total_orders = await count_orders_by_user(user.id) if user else 0
        total_deliveries = await count_orders_by_shipper(shipper.id) if shipper else 0

        # Gộp dữ liệu trả về
        results.append(
            AccountViewOut(
                AccountID=str(acc.id),
                UserID=str(user.id) if user else None,
                ShipperID=str(shipper.id) if shipper else None,
                RoleName=role_name,
                RoleID=str(role.id) if role else None,
                Email=acc.Email,
                FullName=(user.FullName if user else (shipper.FullName if shipper else None)),
                PasswordHash=acc.PasswordHash,
                Phone=(user.Phone if user else (shipper.Phone if shipper else None)),
                Status=acc.Status,
                Address=(user.Address if user else None),
                TotalOrders=total_orders,
                TotalDeliveries=total_deliveries,
                CreatedAt=acc.CreatedAt,
                UpdatedAt=acc.UpdatedAt,
            )
        )
   
    return results


async def count_orders_by_user(user_id):
    return await Order.find(Order.UserID == user_id).count()



async def count_orders_by_shipper(shipper_id):
    return await Shipment.find({"ShipperID" : shipper_id}).count()


