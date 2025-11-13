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
    "Pending": ["Confirmed", "Cancelled"],  # Đã đặt -> Đã xác nhận hoặc Đã hủy
    "Confirmed": ["Processing", "Cancelled"],  # Đã xác nhận -> Đang xử lý hoặc Đã hủy
    "Processing": [
        "Shipped",
        "Cancelled",
    ],  # Đang xử lý -> Đã giao cho vận chuyển hoặc Đã hủy
    "Shipped": [
        "Delivered",
        "Cancelled",
    ],  # Đã giao cho vận chuyển -> Đã giao hoặc Đã hủy
    "Delivered": [],  # Final state - Đã giao
    "Cancelled": [],  # Final state - Đã hủy
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

        # Ensure each order's id is converted to string
        for order in orders:
            if hasattr(order, "id"):
                order.id = str(order.id)

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
    from app.modules.auth.model import Account

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

    # Populate UserName từ Account
    try:
        user_id = order_dict.get("UserID")
        if user_id:
            account = await Account.get(user_id)
            if account and account.profile:
                order_dict["UserName"] = account.profile.fullName
            else:
                order_dict["UserName"] = "Unknown"
        else:
            order_dict["UserName"] = "Unknown"
    except Exception as e:
        print(f"⚠️ Lỗi populate UserName cho order {order_id}: {e}")
        order_dict["UserName"] = "Unknown"

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
    """
    Lấy tổng số đơn hàng theo từng trạng thái (TẤT CẢ đơn hàng, không filter theo ngày).
    Trả về format: {"Pending": 5, "Confirmed": 3, "Processing": 2, "Shipped": 1, "Delivered": 10, "Cancelled": 0}
    """
    try:
        pipeline = [
            # Nhóm theo Status để đếm số lượng đơn hàng
            {"$group": {"_id": "$Status", "count": {"$sum": 1}}},
        ]

        results = await Order.aggregate(pipeline).to_list(None)

        # Tạo summary từ results
        summary = {r["_id"]: r["count"] for r in results if r["_id"]}

        # Đảm bảo tất cả status đều có trong summary (ngay cả nếu count = 0)
        all_statuses = [
            "Pending",
            "Confirmed",
            "Processing",
            "Shipped",
            "Delivered",
            "Cancelled",
        ]
        for status in all_statuses:
            if status not in summary:
                summary[status] = 0

        print(f"📊 Order status summary: {summary}")
        return summary
    except Exception as e:
        print(f"❌ Error getting order status summary: {e}")
        import traceback

        traceback.print_exc()
        # Return default summary with 0 values if error occurs
        return {
            "Pending": 0,
            "Confirmed": 0,
            "Processing": 0,
            "Shipped": 0,
            "Delivered": 0,
            "Cancelled": 0,
        }


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
        {"$match": {"OrderDate": {"$gte": seven_days_ago}, "Status": "Delivered"}},
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
        f"{r['_id']['year']}-{r['_id']['month']:02d}-{r['_id']['day']:02d}": r[
            "revenue"
        ]
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
    """
    Lấy tổng doanh thu hôm nay từ các đơn hàng đã giao (Status = 'Delivered').
    Sử dụng timezone Vietnam (UTC+7).
    """
    from datetime import timezone

    # Sử dụng timezone Vietnam (UTC+7)
    vietnam_tz = timezone(timedelta(hours=7))
    today = datetime.now(vietnam_tz)

    # Tính ngày hôm nay (00:00:00 - 23:59:59 Vietnam time)
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=vietnam_tz)
    end_of_day = start_of_day + timedelta(days=1)

    # Convert sang UTC để so sánh với dữ liệu trong DB
    start_of_day_utc = start_of_day.astimezone(timezone.utc)
    end_of_day_utc = end_of_day.astimezone(timezone.utc)

    pipeline = [
        {
            "$match": {
                "OrderDate": {"$gte": start_of_day_utc, "$lt": end_of_day_utc},
                "Status": "Delivered",  # Chỉ tính đơn hàng đã giao
            }
        },
        {"$group": {"_id": None, "total_revenue": {"$sum": "$TotalAmount"}}},
    ]

    results = await Order.aggregate(pipeline).to_list(None)

    total = results[0]["total_revenue"] if results else 0.0
    print(f"📊 Today's revenue (Delivered orders): {total} VND")
    return total


# lấy đơn hàng mới (status is 'pending') trong ngày hôm nay
async def get_today_pending_orders_count() -> int:
    """
    Trả về số đơn hàng tạo hôm nay và có status là 'pending'.
    Sử dụng timezone Vietnam (UTC+7).
    """
    from datetime import timezone

    # Sử dụng timezone Vietnam (UTC+7)
    vietnam_tz = timezone(timedelta(hours=7))
    today = datetime.now(vietnam_tz)

    # Tính ngày hôm nay (00:00:00 - 23:59:59 Vietnam time)
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=vietnam_tz)
    end_of_day = start_of_day + timedelta(days=1)

    # Convert sang UTC để so sánh với dữ liệu trong DB
    start_of_day_utc = start_of_day.astimezone(timezone.utc)
    end_of_day_utc = end_of_day.astimezone(timezone.utc)

    count = await Order.find(
        {
            "OrderDate": {"$gte": start_of_day_utc, "$lt": end_of_day_utc},
            "Status": "Pending",  # lọc theo trạng thái pending
        }
    ).count()

    print(f"📋 Today's pending orders count: {count}")
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
            "$lt": datetime(year + 1, 1, 1),
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
                "product_name": "$ProductInfo.productName",
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
    1. Có trạng thái là Confirmed hoặc Processing (đã xác nhận hoặc đang xử lý)
    2. Chưa được tạo vận đơn (không tồn tại trong collection Shipments)

    Returns:
        List[Order]: Danh sách đơn hàng đáp ứng điều kiện
    """
    try:
        # Pipeline aggregate để lấy đơn hàng phù hợp
        pipeline = [
            # Stage 1: Chỉ lấy đơn hàng có status phù hợp (Confirmed hoặc Processing)
            {"$match": {"Status": {"$in": ["Processing"]}}},
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


# Lấy danh sách khách hàng thân thiết nhất (top customers)
async def get_top_customers(limit: int = 10) -> List[dict]:
    """
    Lấy danh sách khách hàng thân thiết nhất dựa trên:
    - Tổng số đơn hàng (tất cả trạng thái)
    - Tổng số tiền đã chi tiêu

    Sắp xếp theo tổng số tiền chi tiêu giảm dần.

    Returns:
        List[dict]: Danh sách khách hàng với thông tin:
            - customer_name: Tên khách hàng
            - total_orders: Tổng số đơn hàng
            - total_spent: Tổng số tiền đã chi tiêu
    """
    try:
        # Pipeline aggregate để tính tổng đơn hàng và tổng tiền theo UserID
        pipeline = [
            # Stage 1: Group theo UserID để tính tổng (TẤT CẢ trạng thái)
            {
                "$group": {
                    "_id": "$UserID",
                    "total_orders": {"$sum": 1},
                    "total_spent": {"$sum": "$TotalAmount"},
                }
            },
            # Stage 2: Join với collection accounts để lấy thông tin khách hàng
            {
                "$lookup": {
                    "from": "accounts",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "customer_info",
                }
            },
            # Stage 3: Unwind customer_info
            {"$unwind": "$customer_info"},
            # Stage 4: Chỉ lấy khách hàng có role = "User"
            {"$match": {"customer_info.role": "User"}},
            # Stage 5: Project các trường cần thiết
            {
                "$project": {
                    "_id": 0,
                    "user_id": {"$toString": "$_id"},
                    "customer_name": "$customer_info.profile.fullName",
                    "total_orders": 1,
                    "total_spent": 1,
                }
            },
            # Stage 6: Sắp xếp theo total_spent giảm dần (khách hàng chi tiêu nhiều nhất)
            {"$sort": SON([("total_spent", -1)])},
            # Stage 7: Giới hạn số lượng
            {"$limit": limit},
        ]

        results = await Order.aggregate(pipeline).to_list(None)

        print(f"✅ Found {len(results)} top customers")

        # Xử lý kết quả: đảm bảo customer_name không rỗng
        processed_results = []
        for r in results:
            customer_name = r.get("customer_name", "").strip()
            if not customer_name:
                customer_name = "Khách hàng không tên"

            processed_results.append(
                {
                    "customer_name": customer_name,
                    "total_orders": r.get("total_orders", 0),
                    "total_spent": float(r.get("total_spent", 0.0)),
                }
            )

        return processed_results

    except Exception as e:
        print(f"❌ Error getting top customers: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting top customers: {str(e)}",
        )
