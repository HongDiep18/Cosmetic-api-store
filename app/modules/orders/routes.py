from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from bson import ObjectId
from beanie import PydanticObjectId

from app.core.deps import require_admin_account, get_current_account
from app.modules.orders.schemas import OrderCreate, OrderOut, OrderStatusUpdate,OrderOutCustom
from app.modules.users.model import User
from app.modules.auth.model import Account
from app.modules.orders.controller import (
    create_order,
    get_user_orders,
    list_all_orders,
    update_order_status,
    get_order_status_summary,
    get_last_7_days_total_revenue,
    get_revenue_by_date,
    get_today_total_revenue,
    get_today_pending_orders_count,
    get_monthly_revenue,
    get_best_selling_products_in_month,
    get_orders_ready_for_shipment,
    get_order_summaries,
    attach_payment_info,
)


router = APIRouter()


def normalize_order_for_response(order) -> dict:
    """Normalize Order object for response, converting ObjectId to string"""
    items_normalized = []
    for item in order.Items:
        # Support both dict and object item representations
        if isinstance(item, dict):
            raw_pid = item.get("ProductID")
            if isinstance(raw_pid, (ObjectId, PydanticObjectId)):
                pid_str = str(raw_pid)
            elif isinstance(raw_pid, str):
                pid_str = raw_pid
            else:
                pid_str = str(raw_pid) if raw_pid is not None else ""

            items_normalized.append(
                {
                    "ProductID": pid_str,
                    "Quantity": int(item.get("Quantity", 0)),
                    "Price": float(item.get("Price", 0.0)),
                }
            )
        else:
            product_id = getattr(item, "ProductID", None)
            # Convert ObjectId or PydanticObjectId to string
            if isinstance(product_id, (ObjectId, PydanticObjectId)):
                product_id = str(product_id)
            elif not isinstance(product_id, str):
                product_id = str(product_id) if product_id is not None else ""

            items_normalized.append(
                {
                    "ProductID": product_id,
                    "Quantity": int(getattr(item, "Quantity", 0)),
                    "Price": float(getattr(item, "Price", 0.0)),
                }
            )

    # Build order dict
    order_dict = {
        "_id": str(order.id),
        "OrderID": str(order.OrderID) if hasattr(order, "OrderID") else str(order.id),
        "UserID": str(order.UserID) if order.UserID else "",
        "ShippingAddress": order.ShippingAddress,
        "OrderDate": order.OrderDate,
        "TotalAmount": order.TotalAmount,
        "Status": order.Status.value
        if hasattr(order.Status, "value")
        else str(order.Status),
        "Items": items_normalized,
        "CreatedAt": order.CreatedAt,
        "UpdatedAt": order.UpdatedAt,
    }
    return order_dict


# create order test
# @router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
# async def create_order_endpoint(
#     data: OrderCreate,
#     # current_user: User = Depends(get_current_account)
# ):
#     try:
#         # order = await create_order(user_id=str(current_user.id), data=data)
#         test_user_id = "7027bdf6-be3d-42a9-8ed3-9ecc8a41ca45"

#         order = await create_order(user_id=test_user_id, data=data)
#         return OrderOut.model_validate(order, from_attributes=True)

#     except ValueError as ve:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
#         )


# create order
@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    data: OrderCreate, current_account: User = Depends(get_current_account)
):
    try:
        # Tìm User từ AccountID
        user = await User.find_one(User.AccountID == current_account.AccountID)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        order = await create_order(user_id=str(user.UserID), data=data)
        return OrderOut.model_validate(order, from_attributes=True)

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# get 1 order - user view order of them
@router.get("/get-order", response_model=list[OrderOut])
async def get_my_orders(current_account: Account = Depends(get_current_account)):
    try:
        # Tìm User từ AccountID
        user = await User.find_one(User.AccountID == current_account.AccountID)
        if not user:
            print(f"⚠️ User not found for AccountID={current_account.AccountID}")
            return []

        user_id_str = user.id
        print(f"🔍 Looking for orders with UserID={user_id_str}")
        orders = await get_user_orders(user_id_str)

        if not orders:
            print(f"⚠️ No orders found for UserID={user_id_str}")
            return []

        print(f"✅ Found {len(orders)} orders for UserID={user_id_str}")
        results = []
        for o in orders:
            try:
                results.append(OrderOut.model_validate(o, from_attributes=True))
            except Exception as e:
                print(
                    f"⚠️ model_validate from_attributes=True failed: {e}. Retrying with from_attributes=False"
                )
                results.append(OrderOut.model_validate(o, from_attributes=False))
        return results
    except Exception as e:
        print(f"❌ Error in get_my_orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}",
        )


# get all orders
@router.get("/list-orders", response_model=list[OrderOut])
async def get_list_all_orders(
    # current_user: User = Depends(get_current_account)
):
    try:
        orders = await list_all_orders()

        if not orders:
            return []
        results = []
        for o in orders:
            try:
                # Try attribute-based validation (Beanie Document)
                results.append(OrderOut.model_validate(o, from_attributes=True))
            except Exception:
                # Fallback: validate from plain dict/object mapping
                results.append(OrderOut.model_validate(o, from_attributes=False))

        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}",
        )



@router.get("/list-orders-custom", response_model=list[OrderOutCustom])
async def get_list_all_orders(
):
    try:
        orders = await list_all_orders()

        if not orders:
            return []
        results = []
        for o in orders:
            o = await attach_payment_info(o)

            try:
                # Try attribute-based validation (Beanie Document)
                results.append(OrderOutCustom.model_validate(o, from_attributes=True))
            except Exception:
               # Nếu 1 đơn nào đó bị lỗi payment hoặc validation thì log lại, bỏ qua lỗi
                print(f"⚠️ Lỗi xử lý order {getattr(o, '_id', 'unknown')}: {e}")
                # Vẫn thêm đơn đó nhưng không có payment
                order_dict = o.dict() if hasattr(o, "dict") else dict(o)
                order_dict.update({
                    "PaymentID": None,
                    "PaymentMethod": None,
                    "PaymentStatus": None
                })
                results.append(OrderOutCustom.model_validate(order_dict, from_attributes=False))
                

        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving orders: {str(e)}",
        )


# get status of shipment
@router.get("/ready-for-shipment", response_model=List[OrderOut])
async def get_ready_for_shipment_endpoint():
    """
    Lấy danh sách đơn hàng sẵn sàng để tạo vận đơn:
    - Có trạng thái là Confirmed hoặc Processing
    - Chưa được tạo vận đơn trước đây
    """
    try:
        orders = await get_orders_ready_for_shipment()
        if not orders:
            return []

        return [
            OrderOut.model_validate(order, from_attributes=True) for order in orders
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting orders ready for shipment: {str(e)}",
        )


@router.get(
    "/", response_model=List[OrderOut], dependencies=[Depends(require_admin_account)]
)
async def list_orders_endpoint():
    orders = await list_all_orders()
    results = []
    for o in orders:
        try:
            results.append(OrderOut.model_validate(o, from_attributes=True))
        except Exception:
            results.append(OrderOut.model_validate(o, from_attributes=False))

    return results


# Update order status
@router.patch(
    "/{order_id}/status",
    # response_model=OrderOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_status_endpoint(
    order_id: str,
    status_data: OrderStatusUpdate,
):
    """
    Update an order's status.

    Valid status values:
    - Pending
    - Confirmed
    - Processing
    - Shipped
    - Delivered
    - Failed
    - Cancelled

    Request body example:
    {
        "Status": "Confirmed"
    }
    """
    try:
        # Extract status from request body (OrderStatus enum -> string)
        new_status = status_data.Status.value

        order = await update_order_status(order_id, new_status)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Normalize Order object (convert ObjectId to string)
        order_dict = normalize_order_for_response(order)
        return order_dict

    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# Get status summary
@router.get("/status-summary")
async def get_status_summary_endpoint():
    summary = await get_order_status_summary()
    return summary


# Route lấy doanh thu 7 ngày qua
@router.get("/revenue-last-7-days")
async def revenue_last_7_days_endpoint():
    revenue = await get_last_7_days_total_revenue()
    return {"total_revenue": revenue}


# Route lấy doanh thu theo ngày (YYYY-MM-DD)
@router.get("/revenue-by-date")
async def revenue_by_date_endpoint(date: str):
    """
    Lấy doanh thu của 1 ngày cụ thể (theo định dạng YYYY-MM-DD).
    """
    revenue = await get_revenue_by_date(date)
    return {"revenue_by_date": revenue}


# Route lấy doanh thu hôm nay
@router.get("/revenue-today")
async def revenue_today_endpoint():
    total_revenue = await get_today_total_revenue()
    return {"total_revenue": total_revenue}


# get số đơn hàng hôm nay với status 'pending'
@router.get("/new-orders-today")
async def new_orders_today_endpoint():
    """
    Số đơn hàng hôm nay với status 'pending'
    """
    count = await get_today_pending_orders_count()
    return {"new_orders_today": count}


# Route doanh thu từng tháng
@router.get("/revenue-monthly")
async def revenue_monthly_endpoint(
    year: int | None = Query(None, description="Năm cần lấy doanh thu"),
):
    """
    Lấy doanh thu từng tháng của một năm.
    Nếu không truyền year, lấy tất cả các năm.
    """
    revenue = await get_monthly_revenue(year)
    return {"monthly_revenue": revenue}


# lấy danh sách sản phẩm bán chạy nhất trong tháng
@router.get("/best-selling-products")
async def best_selling_products_endpoint(
    year: int | None = Query(None, description="Năm cần thống kê"),
    month: int | None = Query(None, description="Tháng cần thống kê (1-12)"),
):
    """
    Lấy danh sách sản phẩm bán chạy nhất:
    - Nếu không truyền year, month → lấy tất cả.
    - Nếu có → lọc theo tháng cụ thể.
    """
    products = await get_best_selling_products_in_month(year, month)
    return {"best_selling_products": products}


# Trang
@router.get("/order-summary")
async def get_order_summary_endpoint():
    """
    Lấy danh sách đơn hàng gồm ID, địa chỉ, ngày đặt, tổng số lượng và tổng tiền.
    """
    try:
        summaries = await get_order_summaries()
        return {"orders": summaries}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving order summary: {str(e)}",
        )
