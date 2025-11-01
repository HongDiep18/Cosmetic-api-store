from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_admin_account
from app.modules.orders.schemas import OrderCreate, OrderOut
from app.modules.orders.controller import (
    create_order,
    get_user_orders,
    list_all_orders,
    update_order_status,
)

router = APIRouter()


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    data: OrderCreate,
    # current_user: User = Depends(get_current_account)
):
    try:
        # order = await create_order(user_id=str(current_user.id), data=data)
        test_user_id = "7027bdf6-be3d-42a9-8ed3-9ecc8a41ca45"

        order = await create_order(user_id=test_user_id, data=data)
        return OrderOut.model_validate(order, from_attributes=True)

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# get orders
@router.get("/list-orders", response_model=list[OrderOut])
async def get_my_orders(
    # current_user: User = Depends(get_current_account)
):
    try:
        test_user_id = "7027bdf6-be3d-42a9-8ed3-9ecc8a41ca45"
        orders = await get_user_orders(user_id=test_user_id)

        if not orders:
            return []

        return [OrderOut.model_validate(o, from_attributes=True) for o in orders]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}",
        )


@router.get(
    "/", response_model=list[OrderOut], dependencies=[Depends(require_admin_account)]
)
async def list_orders_endpoint():
    orders = await list_all_orders()
    return [OrderOut.model_validate(o, from_attributes=True) for o in orders]


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_status_endpoint(order_id: str, status: str):
    order = await update_order_status(order_id, status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return OrderOut.model_validate(order, from_attributes=True)
