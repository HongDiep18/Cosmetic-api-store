from typing import List, Optional
from bson import ObjectId
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from app.modules.shippers.schemas import DeliverySummaryOut

# Tạo connection riêng cho module này
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]


async def list_deliveries_by_shipper(
    shipper_id: Optional[str] = None, status: Optional[str] = None
) -> List[DeliverySummaryOut]:
    """
    Lấy danh sách vận đơn của một shipper hoặc tất cả vận đơn, có thể lọc theo trạng thái

    Args:
        shipper_id (Optional[str]): ID của shipper (None để lấy tất cả)
        status (Optional[str]): Trạng thái vận đơn cần lọc (nếu có)

    Returns:
        List[DeliverySummaryOut]: Danh sách các vận đơn tóm tắt
    """
    # Xây dựng query filter
    filter_query = {}
    if shipper_id:
        filter_query["ShipperID"] = ObjectId(shipper_id)
    if status:
        filter_query["Status"] = status

    # Lấy collection
    shipments_collection = db.get_collection("shipments")

    # Thực hiện aggregation để lấy thông tin cần thiết
    pipeline = [
        {"$match": filter_query},
        {
            "$lookup": {
                "from": "orders",
                "localField": "OrderID",
                "foreignField": "_id",
                "as": "order",
            }
        },
        {"$unwind": "$order"},
        {
            "$lookup": {
                "from": "users",
                "localField": "order.UserID",
                "foreignField": "_id",
                "as": "user",
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "payments",
                "let": {"orderIdString": {"$toString": "$order._id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$OrderID", "$$orderIdString"]}}}
                ],
                "as": "payment",
            }
        },
        {"$unwind": {"path": "$payment", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "ShipmentID": {"$toString": "$_id"},
                "TrackingNumber": {"$ifNull": ["$TrackingNumber", ""]},
                "CustomerName": {"$ifNull": ["$user.FullName", ""]},
                "ShippingAddress": {"$ifNull": ["$order.ShippingAddress", ""]},
                "CODAmount": {
                    "$cond": {
                        "if": {
                            "$and": [
                                {"$ne": ["$payment", None]},
                                {"$eq": ["$payment.PaymentMethod", "COD"]},
                                {"$eq": ["$payment.Status", "Pending"]},
                            ]
                        },
                        "then": {"$ifNull": ["$order.TotalAmount", 0]},
                        "else": 0,
                    }
                },
                "Status": {"$ifNull": ["$Status", ""]},
            }
        },
    ]

    cursor = shipments_collection.aggregate(pipeline)
    deliveries = []

    async for doc in cursor:
        # Convert to DeliverySummaryOut model
        delivery = DeliverySummaryOut(
            ShipmentID=doc["ShipmentID"],
            TrackingNumber=doc.get("TrackingNumber", ""),
            CustomerName=doc.get("CustomerName", ""),
            ShippingAddress=doc.get("ShippingAddress", ""),
            CODAmount=float(doc.get("CODAmount", 0)),
            Status=doc.get("Status", ""),
        )
        deliveries.append(delivery)

    return deliveries
