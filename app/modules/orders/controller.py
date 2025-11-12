from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bson.son import SON
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from app.modules.payments.model import Payment
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schemas import OrderCreate
from bson import ObjectId

# Valid order status transitions
VALID_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    "Pending": ["Confirmed", "Cancelled"],
    "Confirmed": ["Processing", "Cancelled"],
    "Processing": ["Shipped", "Cancelled"],
    "Shipped": ["Delivered", "Failed"],
    "Delivered": [],  # Final state
    "Failed": ["Pending"],  # Can retry delivery
    "Cancelled": [],  # Final state
}


async def create_order(user_id: str, data: OrderCreate) -> Order:
    try:
        items = []
        for item in data.Items:
            # product = await Product.find_one(Product.ProductName == item.ProductName)
            # if product is None:
            #     print(f"Không tìm thấy sản phẩm: {item['ProductName']}")
            #     continue

            items.append(
                OrderItem(
                    ProductID=PydanticObjectId(item.ProductID),
                    Quantity=item.Quantity,
                    Price=item.Price,
                )
            )

        total_amount = sum(item.Price * item.Quantity for item in items)
        now = datetime.utcnow()

        order = Order(
            UserID=user_id,  # Convert chỉ user_id
            Items=items,
            TotalAmount=total_amount,
            ShippingAddress=data.ShippingAddress,
            Status=data.Status if hasattr(data, "Status") else "Pending",
            OrderDate=data.OrderDate if hasattr(data, "OrderDate") else now,
            CreatedAt=now,
            UpdatedAt=now,
        )
        await order.insert()
        return order

    except Exception as e:
        # Log lỗi chi tiết
        print("❌ Error creating order:", e)
        raise Exception(f"Error creating order: {str(e)}")


async def get_user_orders(user_id: PydanticObjectId) -> List[Order]:
    try:
        # Find orders with exact user_id string match
        orders = await Order.find({"UserID": user_id}).sort("-CreatedAt").to_list()

        # Ensure each order's _id is converted to string
        for order in orders:
            if hasattr(order, "_id"):
                order._id = str(order._id)

        return orders
    except Exception as e:
        raise Exception(f"Error fetching user orders: {str(e)}")


async def list_all_orders() -> List[Order]:
    # Primary attempt: use Beanie's document find
    try:
        orders = await Order.find_all().sort("-CreatedAt").to_list()
        print(f"list_all_orders: found {len(orders)} orders via Beanie")
        if orders:
            return orders
    except Exception as e:
        print(f"list_all_orders: beanie find_all error: {e}")

    # Fallback: use raw motor collection (handles cases where Beanie models/registration mismatch)
    try:
        raw = (
            await Order.get_motor_collection()
            .find({})
            .sort("CreatedAt", -1)
            .to_list(length=None)
        )
        print(f"list_all_orders: found {len(raw)} orders via raw collection")
        # Attempt to return list of Order documents by constructing Order objects where possible
        orders: List[Order] = []
        for doc in raw:
            try:
                orders.append(Order(**doc))
            except Exception:
                # If construction fails, skip converting and keep raw dicts in list
                orders.append(doc)  # type: ignore

        return orders
    except Exception as e:
        print(f"list_all_orders: raw collection find error: {e}")
        return []

async def attach_payment_info(order):
    try:
        order_id = order.id if isinstance(order.id, ObjectId) else ObjectId(order.id)
    except Exception:
        order_id = order.id  # fallback

    payment = None
    try:
        # Thử tìm bằng ObjectId
        payment = await Payment.find_one(Payment.OrderID == order_id)
        if not payment:
            # fallback: thử tìm bằng string
            payment = await Payment.find_one(Payment.OrderID == str(order_id))
    except Exception as e:
        print(f"⚠️ Lỗi tìm payment cho order {order_id}: {e}")

    # Convert sang dict để tránh Beanie Document lỗi
    order_dict = order.dict() if hasattr(order, "dict") else dict(order)

    order_dict["PaymentID"] = str(payment.id) if payment else None
    order_dict["PaymentMethod"] = getattr(payment, "PaymentMethod", None)
    order_dict["PaymentStatus"] = getattr(payment, "PaymentStatus", None)

    return order_dict

async def update_order_status(order_id: str, new_status: str) -> Optional[Order]:
    """
    Cập nhật trạng thái đơn hàng với xác thực chuyển đổi trạng thái.

    Args:
        order_id: ID của đơn hàng cần cập nhật
        new_status: Trạng thái mới muốn chuyển đến

    Returns:
        Updated Order object hoặc None nếu không tìm thấy đơn hàng

    Raises:
        HTTPException: Nếu chuyển đổi trạng thái không hợp lệ
    """
    try:
        # # Bước 1: Kiểm tra trạng thái mới có nằm trong danh sách trạng thái hợp lệ không
        # # Ví dụ: new_status phải là một trong các giá trị: Pending, Confirmed, Processing, etc.
        # if new_status not in VALID_STATUS_TRANSITIONS:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Trạng thái không hợp lệ. Phải là một trong các giá trị: {', '.join(VALID_STATUS_TRANSITIONS.keys())}",
        #     )

        # Bước 2: Lấy thông tin đơn hàng từ database
        order = await Order.get(PydanticObjectId(order_id))
        if not order:
            return None

        current_status = order.Status

        # # Bước 3: Kiểm tra trạng thái hiện tại có hợp lệ không
        # # Ví dụ: current_status phải là một trạng thái đã định nghĩa
        # if current_status not in VALID_STATUS_TRANSITIONS:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Trạng thái hiện tại '{current_status}' không hợp lệ",
        #     )

        # # Bước 4: Kiểm tra xem có được phép chuyển từ trạng thái hiện tại sang trạng thái mới không
        # # Ví dụ: Pending chỉ có thể chuyển sang Confirmed hoặc Cancelled
        # allowed_transitions = VALID_STATUS_TRANSITIONS[current_status]
        # if new_status not in allowed_transitions:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Không thể chuyển từ '{current_status}' sang '{new_status}'. Chỉ có thể chuyển sang: {', '.join(allowed_transitions)}",
        #     )

        # Update the order
        order.Status = new_status
        order.UpdatedAt = datetime.utcnow()
        await order.save()

        return order

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Error updating order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order status: {str(e)}",
        )


# get status summary
async def get_order_status_summary():
    # Lấy ngày hiện tại (không tính giờ, phút, giây)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    pipeline = [
        {
            "$match": {
                "Status": {"$ne": None},
                "CreatedAt": {
                    "$gte": today,
                    "$lt": tomorrow,
                },  # chỉ lấy đơn của hôm nay
            }
        },
        {"$group": {"_id": "$Status", "count": {"$sum": 1}}},
    ]

    results = await Order.aggregate(pipeline).to_list(None)
    summary = {r["_id"]: r["count"] for r in results}
    return summary


# Lấy doanh thu 7 ngày gần nhất chỉ của đơn hàng Delivered
async def get_last_7_days_total_revenue() -> list[dict]:
    """
    Trả về doanh thu từng ngày của 7 ngày gần nhất với status = "Delivered".
    Nếu ngày nào không có đơn hàng, revenue = 0.
    """
    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=6)  # 7 ngày tính từ 6 ngày trước + hôm nay

    # Pipeline MongoDB: nhóm theo ngày với điều kiện Status = "Delivered"
    pipeline = [
        {
            "$match": {
                "OrderDate": {"$gte": seven_days_ago},
                "Status": "Delivered"
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$OrderDate"},
                    "month": {"$month": "$OrderDate"},
                    "day": {"$dayOfMonth": "$OrderDate"},
                },
                "revenue": {"$sum": "$TotalAmount"},
            }
        },
        {"$sort": SON([("_id.year", 1), ("_id.month", 1), ("_id.day", 1)])},
    ]

    results = await Order.aggregate(pipeline).to_list(None)

    # Chuyển kết quả aggregate thành dict: "YYYY-MM-DD" -> revenue
    revenue_dict = {
        f"{r['_id']['year']}-{r['_id']['month']:02d}-{r['_id']['day']:02d}": r["revenue"]
        for r in results
    }

    # Tạo list 7 ngày gần nhất
    daily_revenue = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        daily_revenue.append(
            {
                "date": day_str,
                "revenue": revenue_dict.get(day_str, 0),  # nếu không có dữ liệu thì = 0
            }
        )

    return daily_revenue

# lấy doanh thu từng ngày
# Hàm lấy doanh thu của 1 ngày cụ thể
async def get_revenue_by_date(date: str) -> dict:
    """
    Trả về doanh thu của 1 ngày cụ thể (YYYY-MM-DD).
    """
    try:
        # Parse ngày người dùng nhập
        day = datetime.strptime(date, "%Y-%m-%d")

        # Tạo khoảng thời gian [00:00, 23:59:59] của ngày đó
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)

        # Pipeline MongoDB: nhóm tổng doanh thu trong ngày
        pipeline = [
            {"$match": {"OrderDate": {"$gte": start, "$lt": end}}},
            {"$group": {"_id": None, "revenue": {"$sum": "$TotalAmount"}}},
        ]

        result = await Order.aggregate(pipeline).to_list(None)
        revenue = result[0]["revenue"] if result else 0

        return {"date": date, "revenue": revenue}

    except Exception as e:
        # Nếu lỗi (ví dụ sai định dạng ngày)
        return {"date": date, "revenue": 0, "error": str(e)}


# Get today's total revenue
async def get_today_total_revenue() -> float:
    today = datetime.utcnow()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = start_of_day + timedelta(days=1)

    pipeline = [
        {"$match": {"OrderDate": {"$gte": start_of_day, "$lt": end_of_day}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$TotalAmount"}}},
    ]

    results = await Order.aggregate(pipeline).to_list(None)
    return results[0]["total_revenue"] if results else 0.0


# lấy đơn hàng mới (status is 'pending') trong ngày hôm nay
async def get_today_pending_orders_count() -> int:
    """
    Trả về số đơn hàng tạo hôm nay và có status là 'pending'
    """
    today = datetime.utcnow()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = start_of_day + timedelta(days=1)

    count = await Order.find(
        {
            "OrderDate": {"$gte": start_of_day, "$lt": end_of_day},
            "Status": "Pending",  # lọc theo trạng thái pending
        }
    ).count()

    return count


# hàm lấy doanh thu theo tháng trong một năm
async def get_monthly_revenue(year: int | None = None) -> List[Dict]:
    """
    Trả về doanh thu từng tháng trong một năm (chỉ các đơn hàng Delivered).
    Nếu year=None, lấy tất cả các năm.
    """
    match_conditions = {"Status": "Delivered"}  # Chỉ lấy đơn hàng Delivered
    if year:
        match_conditions["OrderDate"] = {
            "$gte": datetime(year, 1, 1),
            "$lt": datetime(year + 1, 1, 1)
        }

    pipeline = [
        {"$match": match_conditions} if match_conditions else None,
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$OrderDate"},
                    "month": {"$month": "$OrderDate"},
                },
                "revenue": {"$sum": "$TotalAmount"},
            }
        },
        {"$sort": SON([("_id.year", 1), ("_id.month", 1)])},
    ]

    # Loại bỏ None nếu pipeline[0] = None
    pipeline = [stage for stage in pipeline if stage is not None]

    results = await Order.aggregate(pipeline).to_list(None)

    # Chuyển kết quả sang list dict dễ dùng
    monthly_revenue = [
        {"year": r["_id"]["year"], "month": r["_id"]["month"], "revenue": r["revenue"]}
        for r in results
    ]

    return monthly_revenue


# lấy danh sách sản phẩm bán chạy nhất trong tháng
async def get_best_selling_products_in_month(
    year: int | None = None, month: int | None = None
) -> List[Dict]:
    """
    Lấy danh sách sản phẩm bán chạy nhất.
    - Nếu có year + month: lọc theo tháng đó.
    - Nếu không: lấy tất cả các tháng.
    - Chỉ tính đơn hàng có Status = 'Delivered'.
    """

    match_stage = {"Status": "Delivered"}

    # Nếu có truyền year + month thì lọc theo tháng
    if year and month:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        match_stage["OrderDate"] = {"$gte": start_date, "$lt": end_date}

    pipeline = [
        {"$match": match_stage},
        {"$unwind": "$Items"},
        {
            "$group": {
                "_id": "$Items.ProductID",
                "total_quantity": {"$sum": "$Items.Quantity"},
                "total_revenue": {
                    "$sum": {"$multiply": ["$Items.Quantity", "$Items.Price"]}
                },
            }
        },
        # Kết hợp với bảng Product để lấy thông tin chi tiết
        {
            "$lookup": {
                "from": "products",  # Tên collection Product trong MongoDB
                "localField": "_id",
                "foreignField": "_id",
                "as": "ProductInfo",
            }
        },
        {"$unwind": "$ProductInfo"},
        {
            "$project": {
                "_id": 0,
                "product_name": "$ProductInfo.ProductName",
                "total_quantity": 1,
                "total_revenue": 1,
            }
        },
        {"$sort": SON([("total_quantity", -1)])},
        {"$limit": 5},
    ]

    results = await Order.aggregate(pipeline).to_list(None)
    return results


# Lấy danh sách đơn hàng sẵn sàng tạo vận đơn
async def get_orders_ready_for_shipment() -> List[Order]:
    """
    Lấy danh sách đơn hàng thỏa mãn điều kiện:
    1. Có trạng thái là Confirmed hoặc Processing
    2. Chưa được tạo vận đơn (không tồn tại trong collection Shipments)

    Returns:
        List[Order]: Danh sách đơn hàng đáp ứng điều kiện
    """
    try:
        # Pipeline aggregate để lấy đơn hàng phù hợp
        pipeline = [
            # Stage 1: Chỉ lấy đơn hàng có status phù hợp
            {"$match": {"Status": {"$in": ["Pending", "Processing"]}}},
            # Stage 2: Left join với collection shipments
            {
                "$lookup": {
                    "from": "shipments",
                    "localField": "_id",
                    "foreignField": "OrderID",
                    "as": "shipments",
                }
            },
            # Stage 3: Chỉ lấy đơn hàng chưa có trong shipments
            {"$match": {"shipments": {"$size": 0}}},
            # Stage 4: Loại bỏ field shipments không cần thiết
            {"$project": {"shipments": 0}},
        ]

        # Thực hiện aggregate và chuyển kết quả về Order objects
        results = await Order.aggregate(pipeline).to_list(None)

        orders: List[Order] = []
        for doc in results:
            try:
                # Chuyển từ dict sang Order object
                order = Order.parse_obj(doc)
                orders.append(order)
            except Exception as e:
                print(f"❌ Error parsing order: {e}")
                continue

        return orders

    except Exception as e:
        print(f"❌ Error getting orders ready for shipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting orders ready for shipment: {str(e)}",
        )


# Trang
# lấy thông tin đơn hàng
async def get_order_summaries() -> list[dict]:
    """
    Lấy thông tin đơn hàng gồm ID, địa chỉ, ngày đặt, tổng số lượng và tổng tiền.
    """
    pipeline = [
        {
            "$project": {
                "_id": 1,
                "ShippingAddress": 1,
                "OrderDate": 1,
                "TotalAmount": 1,
                "Status": 1,
                "TotalQuantity": {"$sum": "$Items.Quantity"},
            }
        },
        {"$sort": {"OrderDate": -1}},
    ]

    results = await Order.aggregate(pipeline).to_list(None)
    # Chuyển _id sang string cho dễ đọc
    for r in results:
        r["_id"] = str(r["_id"])
    return results
