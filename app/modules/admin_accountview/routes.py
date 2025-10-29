# # app/modules/admin_accountview/routes.py
# from fastapi import APIRouter, HTTPException, status
# from app.modules.admin_accountview.controller import (
#     get_all_customers,
#     get_all_shippers,
# )
# from app.modules.admin_accountview.schemas import (
#     CustomerOut,
#     ShipperOut,
# )

# router = APIRouter()

# # ------------------- ADMIN ROUTES -------------------


# @router.get(
#     "/accountview/customers",
#     response_model=list[CustomerOut],
#     # dependencies=[Depends(require_admin_account)]
# )
# async def list_customers():
#     """
#     🧾 Lấy danh sách khách hàng (Admin)
#     """
#     try:
#         customers = await get_all_customers()
#         if not customers:
#             return []
#         return customers
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching customers: {str(e)}",
#         )


# @router.get(
#     "/accountview/shippers",
#     response_model=list[ShipperOut],
#     # dependencies=[Depends(require_admin_account)]
# )
# async def list_shippers():
#     """
#     🚚 Lấy danh sách shipper (Admin)
#     """
#     try:
#         shippers = await get_all_shippers()
#         if not shippers:
#             return []
#         return shippers
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching shippers: {str(e)}",
#         )
