# from fastapi import APIRouter, Depends, HTTPException, status

# from app.core.deps import get_current_account, require_admin_account
# from app.modules.users.model import User
# from app.modules.orders.schemas import OrderCreate, OrderOut
# from app.modules.orders.controller import (
#     create_order,
#     get_user_orders,
#     list_all_orders,
#     update_order_status,
# )

# router = APIRouter()


# @router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
# async def create_order_endpoint(
#     data: OrderCreate, current_user: User = Depends(get_current_account)
# ):
#     order = await create_order(user_id=str(current_user.id), data=data)
#     return OrderOut.model_validate(order, from_attributes=True)


# @router.get("/my-orders", response_model=list[OrderOut])
# async def get_my_orders(current_user: User = Depends(get_current_account)):
#     orders = await get_user_orders(user_id=str(current_user.id))
#     return [OrderOut.model_validate(o, from_attributes=True) for o in orders]


# @router.get(
#     "/", response_model=list[OrderOut], dependencies=[Depends(require_admin_account)]
# )
# async def list_orders_endpoint():
#     orders = await list_all_orders()
#     return [OrderOut.model_validate(o, from_attributes=True) for o in orders]


# @router.patch(
#     "/{order_id}/status",
#     response_model=OrderOut,
#     dependencies=[Depends(require_admin_account)],
# )
# async def update_status_endpoint(order_id: str, status: str):
#     order = await update_order_status(order_id, status)
#     if not order:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
#         )
#     return OrderOut.model_validate(order, from_attributes=True)
