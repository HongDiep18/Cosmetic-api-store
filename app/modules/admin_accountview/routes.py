# app/modules/admin_accountview/routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import require_admin_account
from app.modules.admin_accountview.controller import (
    get_all_customers,
    get_all_shippers,
    get_account_custom
)
from app.modules.admin_accountview.schemas import (
    CustomerOut,
    ShipperOut,
    AccountOut
)

router = APIRouter(tags=["Admin Account View"])

# ------------------- ADMIN ROUTES -------------------

@router.get("/accountview/customers",
            response_model=list[CustomerOut],
            # dependencies=[Depends(require_admin_account)]
            )
async def list_customers():
    """
    🧾 Lấy danh sách khách hàng (Admin)
    """
    customers = await get_all_customers()
    return customers


@router.get("/accountview/shippers",
            response_model=list[ShipperOut],
            # dependencies=[Depends(require_admin_account)]
            )
async def list_shippers():
    """
    🚚 Lấy danh sách shipper (Admin)
    """
    shippers = await get_all_shippers()
    return shippers

@router.get("/accountview/accounts",
            response_model=list[AccountOut],
            )
async def list_account():
    Account  = await get_account_custom()
    return Account