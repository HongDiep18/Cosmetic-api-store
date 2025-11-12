from typing import Optional, List
import traceback
from bson import ObjectId
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.modules.shipments.model import Shipment
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.modules.auth.model import Account
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
    """Return aggregated delivery details for a shipment or order.

    Inputs:
      - shipment_id: string (hex ObjectId) - can be either ShipmentID or OrderID
      - current_shipper_id: optional shipper id string for authorization

    Output: DeliveryDetailsOut (raises HTTPException on errors)
    """
    try:
        # Validate ID format
        try:
            obj_id = PydanticObjectId(shipment_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID format: {e}",
            )

        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]
        order = None
        shipment = None
        order_id = None
        tracking_number = "N/A"
        shipment_status = "Unknown"

        # Strategy 1: Try to find shipment by ID first
        try:
            shipment = await Shipment.get(obj_id)
            if shipment and shipment.OrderID:
                order_id = shipment.OrderID
                tracking_number = getattr(shipment, "TrackingNumber", "N/A") or "N/A"
                shipment_status = str(getattr(shipment, "Status", "Unknown"))
                # Load order from shipment
                order = await db["orders"].find_one({"_id": order_id})
        except Exception as e:
            print(f"⚠️ Shipment lookup by ID failed: {e}")

        # Strategy 2: If order not found, try to find order directly by ID
        if not order:
            try:
                order = await db["orders"].find_one({"_id": obj_id})
                if order:
                    order_id = obj_id
                    # Try to find associated shipment by OrderID
                    try:
                        shipment_dict = await db["shipments"].find_one(
                            {"OrderID": obj_id}
                        )
                        if shipment_dict:
                            tracking_number = (
                                shipment_dict.get("TrackingNumber", "N/A") or "N/A"
                            )
                            shipment_status = str(
                                shipment_dict.get("Status", "Unknown")
                            )
                    except Exception as e:
                        print(f"⚠️ Associated shipment lookup failed: {e}")
            except Exception as e:
                print(f"⚠️ Order lookup by ID failed: {e}")

        # If order still not found, return error
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order not found with ID: {shipment_id}. Please verify the ID is correct.",
            )

        # Load customer (UserID đã được migration thành Account._id)
        if not order.get("UserID"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order has no associated user ID",
            )

        customer = await Account.get(order.get("UserID"))
        if not customer or customer.role != "User":
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
            TrackingNumber=tracking_number,
            ShipmentStatus=shipment_status,
            OrderID=str(order.get("_id", "")),
            ShippingAddress=order.get("ShippingAddress", ""),
            TotalAmount=float(order.get("TotalAmount", 0.0)),
            OrderStatus=order.get("Status", "Unknown"),
            CustomerName=customer.profile.fullName if customer.profile else "",
            CustomerPhone=customer.profile.phone if customer.profile else "N/A",
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
                "from": "accounts",
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
                "OrderID": {"$toString": "$order._id"},
                "TrackingNumber": {"$ifNull": ["$TrackingNumber", ""]},
                "CustomerName": {"$ifNull": ["$user.profile.fullName", ""]},
                "CustomerPhone": {"$ifNull": ["$user.profile.phone", ""]},
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
                "Status": {"$ifNull": ["$order.Status", "$Status", ""]},
                "Items": {"$ifNull": ["$order.Items", []]},
            }
        },
    ]

    cursor = shipments_collection.aggregate(pipeline)
    deliveries = []

    async for doc in cursor:
        # Process items
        items = []
        for item in doc.get("Items", []):
            try:
                # Extract product info
                product_id = str(item.get("ProductID", ""))

                # Try to get product name
                product_name = "Unknown Product"
                try:
                    if product_id:
                        product_obj_id = PydanticObjectId(product_id)
                        product = await Product.get(product_obj_id)
                        if product:
                            product_name = getattr(
                                product, "ProductName", "Unknown Product"
                            )
                except Exception:
                    pass

                items.append(
                    OrderItemDetail(
                        ProductID=product_id,
                        ProductName=product_name,
                        Quantity=int(item.get("Quantity", 0)),
                        Price=float(item.get("Price", 0.0)),
                    )
                )
            except Exception as e:
                print(f"Error processing item: {e}")
                continue

        # Convert to DeliverySummaryOut model
        delivery = DeliverySummaryOut(
            ShipmentID=doc["ShipmentID"],
            OrderID=doc.get(
                "OrderID", doc["ShipmentID"]
            ),  # Fallback to ShipmentID if OrderID missing
            TrackingNumber=doc.get("TrackingNumber", ""),
            CustomerName=doc.get("CustomerName", ""),
            CustomerPhone=doc.get("CustomerPhone", ""),
            ShippingAddress=doc.get("ShippingAddress", ""),
            CODAmount=float(doc.get("CODAmount", 0)),
            Status=doc.get("Status", ""),
            Items=items,
        )
        deliveries.append(delivery)

    return deliveries
