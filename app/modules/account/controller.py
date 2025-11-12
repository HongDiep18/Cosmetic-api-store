# app/modules/admin_accountview/controller.py
from app.modules.auth.model import Account
from app.modules.shipments.model import Shipment
from app.modules.account.schemas import AccountViewOut
from app.modules.orders.model import Order


# ------------------- ACCOUNT VIEW -------------------
async def get_account_custom():
    accounts = await Account.find_all().to_list()
    results = []

    for acc in accounts:
        # Lấy thống kê tương ứng
        total_orders = 0
        total_deliveries = 0

        if acc.role == "User":
            total_orders = await count_orders_by_user(str(acc.id))
        elif acc.role == "Shipper":
            total_deliveries = await count_orders_by_shipper(str(acc.id))

        # Gộp dữ liệu trả về
        results.append(
            AccountViewOut(
                _id=str(acc.id),
                email=acc.email,
                role=acc.role,
                status=acc.status,
                profile={
                    "fullName": acc.profile.fullName,
                    "phone": acc.profile.phone,
                    "address": acc.profile.address,
                },
                passwordResetToken=acc.passwordResetToken,
                passwordResetExpires=acc.passwordResetExpires,
                createdAt=acc.createdAt,
                updatedAt=acc.updatedAt,
                TotalOrders=total_orders,
                TotalDeliveries=total_deliveries,
            )
        )

    return results


async def count_orders_by_user(account_id):
    return await Order.find(Order.UserID == account_id).count()


async def count_orders_by_shipper(account_id):
    return await Shipment.find({"ShipperID": account_id}).count()
