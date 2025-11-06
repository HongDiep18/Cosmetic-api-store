from __future__ import annotations
from typing import List, Optional
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schemas import OrderCreate
from datetime import datetime, timedelta
from typing import Dict
from bson.son import SON
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from app.modules.products.model import Product  # Giả sử bạn có model Product để truy vấn sản phẩm
async def create_order(user_id: str, data: OrderCreate) -> Order:
    try:
        from beanie import PydanticObjectId
        
        items = []
        for item in data.Items:
            items.append(
                OrderItem(
                    ProductID=item.ProductID,
                    Quantity=item.Quantity,
                    Price=item.Price,
                )
            )

        total_amount = sum(item.Price * item.Quantity for item in items)
        now = datetime.utcnow()

        # Convert user_id to PydanticObjectId
        try:
            user_oid = PydanticObjectId(user_id)
        except Exception:
            user_oid = user_id  # Fallback to string if conversion fails
    
        order = Order(
            UserID=user_oid,
            Items=items,
            TotalAmount=total_amount,
            ShippingAddress=data.ShippingAddress,
            Status=data.Status if hasattr(data, "Status") else "Pending",
            OrderDate=data.OrderDate if hasattr(data, "OrderDate") else now,
            CreatedAt=now,
            UpdatedAt=now,
        )
        await order.insert()
        print(f"✅ Created order for user_id={user_id} (oid={user_oid}), order_id={order.OrderID}")
        return order

    except Exception as e:
        # Log lỗi chi tiết
        print("❌ Error creating order:", e)
        raise Exception(f"Error creating order: {str(e)}")


async def get_user_orders(user_id: str) -> List[Order]:
    try:
        # Convert string user_id to PydanticObjectId for query
        from beanie import PydanticObjectId
        try:
            user_oid = PydanticObjectId(user_id)
        except Exception:
            # If user_id is not a valid ObjectId, try to find by string
            user_oid = user_id
        
        # Find orders with UserID matching (handles both ObjectId and string)
        orders = await Order.find(
            {"$or": [
                {"UserID": user_oid},
                {"UserID": user_id}
            ]}
        ).sort("-CreatedAt").to_list()

        print(f"🔍 get_user_orders: user_id={user_id}, found {len(orders)} orders")

        # Ensure each order's _id is converted to string
        for order in orders:
            if hasattr(order, "_id"):
                order._id = str(order._id)

        return orders
    except Exception as e:
        print(f"❌ Error in get_user_orders: {e}")
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


async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    order = await Order.get(order_id)
    if not order:
        return None
    order.Status = status
    await order.save()
    return order


# get status summary
async def get_order_status_summary():
    # Lấy ngày hiện tại (không tính giờ, phút, giây)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    pipeline = [
        {
            "$match": {
                "Status": {"$ne": None},
                "CreatedAt": {"$gte": today, "$lt": tomorrow}  # chỉ lấy đơn của hôm nay
            }
        },
        {
            "$group": {
                "_id": "$Status",
                "count": {"$sum": 1}
            }
        }
    ]

    results = await Order.aggregate(pipeline).to_list(None)
    summary = {r["_id"]: r["count"] for r in results}
    return summary

# # ====== Lấy chi tiết 1 đơn hàng ======
# async def get_order_details(order_id: str) -> Dict[str, Any]:
#     """
#     Lấy thông tin chi tiết của một đơn hàng theo ID:
#     - Mã đơn hàng
#     - Tên khách hàng
#     - Danh sách sản phẩm, số lượng, giá
#     - Tổng tiền
#     - Ngày đặt
#     """
#     try:
#         object_id = ObjectId(order_id)
#     except:
#         raise HTTPException(status_code=400, detail="Mã đơn hàng không hợp lệ")

#     pipeline = [
#         {"$match": {"_id": object_id}},
#         {
#             "$lookup": {
#                 "from": "users",
#                 "localField": "UserID",
#                 "foreignField": "_id",
#                 "as": "UserInfo",
#             }
#         },
#         {"$unwind": {"path": "$UserInfo", "preserveNullAndEmptyArrays": True}},
#         {"$unwind": "$Items"},
#         {
#             "$lookup": {
#                 "from": "products",
#                 "localField": "Items.ProductID",
#                 "foreignField": "_id",
#                 "as": "ProductInfo",
#             }
#         },
#         {"$unwind": {"path": "$ProductInfo", "preserveNullAndEmptyArrays": True}},
#         {
#             "$group": {
#                 "_id": "$_id",
#                 "customer_name": {"$first": "$UserInfo.FullName"},
#                 "order_date": {"$first": "$OrderDate"},
#                 "total_amount": {"$first": "$TotalAmount"},
#                 "status": {"$first": "$Status"},
#                 "items": {
#                     "$push": {
#                         "product_name": "$ProductInfo.ProductName",
#                         "quantity": "$Items.Quantity",
#                         "price": "$Items.Price",
#                     }
#                 },
#             }
#         },
#     ]

#     result = await Order.aggregate(pipeline).to_list(None)
#     if not result:
#         raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

#     return result[0]

# lấy doanh thu 7 ngày gần nhất
async def get_last_7_days_total_revenue() -> list[dict]:
    """
    Trả về doanh thu từng ngày của 7 ngày gần nhất.
    Nếu ngày nào không có đơn hàng, revenue = 0.
    """
    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=6)  # 7 ngày tính từ 6 ngày trước + hôm nay

    # Pipeline MongoDB: nhóm theo ngày
    pipeline = [
        {"$match": {"OrderDate": {"$gte": seven_days_ago}}},
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
    Trả về doanh thu từng tháng trong một năm.
    Nếu year=None, lấy tất cả các năm.
    """
    match_stage = {}
    if year:
        match_stage["$match"] = {
            "OrderDate": {"$gte": datetime(year, 1, 1), "$lt": datetime(year + 1, 1, 1)}
        }

    pipeline = []
    if match_stage:
        pipeline.append(match_stage)

    pipeline.extend(
        [
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
    )

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


