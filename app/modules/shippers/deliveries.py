from typing import Optional, List
import traceback
from bson import ObjectId
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.modules.shipments.model import Shipment
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.modules.users.model import User
from app.modules.products.model import Product
from app.modules.shippers.schemas import (
    DeliveryDetailsOut,
    OrderItemDetail,
    DeliverySummaryOut,
)

# Tạo connection riêng cho module này
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]


# async def _to_pydantic_object_id(val: Optional[str]):
#     """Safely convert a string to PydanticObjectId or return None."""
#     if not val:
#         return None
#     try:
#         return PydanticObjectId(val)
#     except Exception:
#         # If it's already an ObjectId-like, try using it directly
#         try:
#             return PydanticObjectId(str(val))
#         except Exception:
#             return None


async def get_delivery_details(
    shipment_id: str, current_shipper_id: Optional[str] = None
) -> DeliveryDetailsOut:
    """Return aggregated delivery details for a shipment.

    Inputs:
      - shipment_id: string (hex ObjectId)
      - current_shipper_id: optional shipper id string for authorization

    Output: DeliveryDetailsOut (raises HTTPException on errors)
    """
    try:
        # Convert shipment id
        try:
            shipment_obj_id = PydanticObjectId(shipment_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid shipment ID format: {e}",
            )

        # Load shipment
        shipment = await Shipment.get(shipment_obj_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment not found with ID: {shipment_id}",
            )

        # Authorization check (if provided)
        # if current_shipper_id and str(shipment.ShipperID) != current_shipper_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to view this delivery",
        #     )

        # Load order using motor to avoid validation errors when ProductID stored
        # as ObjectId while Order model expects string ProductID.
        if not shipment.OrderID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment has no associated order ID",
            )

        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]
        order = await db["orders"].find_one({"_id": shipment.OrderID})
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order not found with ID: {shipment.OrderID}",
            )

        # Load customer (UserID may be ObjectId)
        if not order.get("UserID"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order has no associated user ID",
            )

        customer = await User.get(order.get("UserID"))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found with ID: {order.get('UserID')}",
            )

        # Payment and COD calculation
        payment = await db["payments"].find_one({"OrderID": str(order.get("_id"))})
        cod_amount = 0.0
        payment_method = "Unknown"
        payment_status = "Unknown"
        if payment:
            if isinstance(payment, dict):
                payment_method = payment.get("PaymentMethod", "Unknown")
                payment_status = payment.get("Status", "Unknown")
            else:
                payment_method = getattr(payment, "PaymentMethod", "Unknown")
                payment_status = getattr(payment, "Status", "Unknown")

            if payment_status == "Pending" and payment_method == "COD":
                cod_amount = float(order.get("TotalAmount", 0.0))

        # Process items
        items: List[OrderItemDetail] = []
        for item in order.get("Items", []):
            try:
                # item is a raw dict from MongoDB; ProductID may be ObjectId
                raw_pid = (
                    item.get("ProductID")
                    if isinstance(item, dict)
                    else getattr(item, "ProductID", None)
                )
                product = None
                product_name = "Unknown Product"

                if raw_pid is not None:
                    pid_str = str(raw_pid)
                    # Try lookup by ObjectId/string
                    try:
                        product_obj_id = PydanticObjectId(pid_str)
                        product = await Product.get(product_obj_id)
                    except Exception:
                        try:
                            product = await Product.get(pid_str)
                        except Exception:
                            product = None

                    if product:
                        product_name = getattr(
                            product, "ProductName", "Unknown Product"
                        )

                items.append(
                    OrderItemDetail(
                        ProductID=str(raw_pid),
                        ProductName=product_name,
                        Quantity=int(
                            item.get("Quantity", 0)
                            if isinstance(item, dict)
                            else getattr(item, "Quantity", 0)
                        ),
                        Price=float(
                            item.get("Price", 0.0)
                            if isinstance(item, dict)
                            else getattr(item, "Price", 0.0)
                        ),
                    )
                )
            except Exception as e:
                # Log and continue with other items
                print(
                    f"Error processing order item {getattr(item, 'ProductID', None)}: {e}"
                )
                traceback.print_exc()
                continue

        # Build response
        response = DeliveryDetailsOut(
            TrackingNumber=getattr(shipment, "TrackingNumber", "N/A") or "N/A",
            ShipmentStatus=str(getattr(shipment, "Status", "Unknown")),
            OrderID=str(order.get("_id", "")),
            ShippingAddress=order.get("ShippingAddress", ""),
            TotalAmount=float(order.get("TotalAmount", 0.0)),
            OrderStatus=order.get("Status", "Unknown"),
            CustomerName=getattr(customer, "FullName", ""),
            CustomerPhone=getattr(customer, "Phone", "N/A") or "N/A",
            Items=items,
            CODAmount=cod_amount,
            PaymentMethod=payment_method,
            PaymentStatus=payment_status,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_delivery_details: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


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
