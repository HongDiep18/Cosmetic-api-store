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
        
        items = []
        for item in data.Items:
            
            # product = await Product.find_one(Product.ProductName == item.ProductName)
            # if product is None:
            #     print(f"Không tìm thấy sản phẩm: {item['ProductName']}")
            #     continue

            items.append(
                OrderItem(
                    ProductID=item.ProductID,
                    Quantity=item.Quantity,
                    Price=item.Price,
                )
            )

        total_amount = sum(item.Price * item.Quantity for item in items)
        now = datetime.utcnow()


    
        order = Order(
            UserID=user_id, # Convert chỉ user_id
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


async def get_user_orders(user_id: str) -> List[Order]:
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


async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    order = await Order.get(order_id)
    if not order:
        return None
    order.Status = status
    await order.save()
    return order


# get status summary


async def get_order_status_summary():
    pipeline = [
        {"$match": {"Status": {"$ne": None}}},  # lọc những đơn hàng có status
        {"$group": {"_id": "$Status", "count": {"$sum": 1}}},
    ]
    results = await Order.aggregate(pipeline).to_list(None)

    summary = {r["_id"]: r["count"] for r in results}
    return summary


# Get revenue for the last 7 days
# async def get_last_7_days_total_revenue() -> float:
#     today = datetime.utcnow()
#     seven_days_ago = today - timedelta(days=7)

#     pipeline = [
#         {"$match": {"OrderDate": {"$gte": seven_days_ago}}},
#         {"$group": {"_id": None, "total_revenue": {"$sum": "$TotalAmount"}}}
#     ]

#     results = await Order.aggregate(pipeline).to_list(None)
#     return results[0]["total_revenue"] if results else 0.0


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
