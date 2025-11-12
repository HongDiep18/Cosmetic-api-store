from typing import List, Optional

from app.modules.shipments.model import Shipment
from app.modules.shipments.schemas import ShipmentUpdate, ShipmentStatus
from enum import Enum as _Enum


async def create_shipment(shipment_data: dict) -> Optional[Shipment]:
    try:
        shipment = Shipment(**shipment_data)
        await shipment.insert()
        return shipment
    except Exception as e:
        print(f"Error creating shipment: {str(e)}")
        return None


async def get_shipment(shipment_id: str) -> Optional[Shipment]:
    return await Shipment.get(shipment_id)


async def get_shipments_by_order(order_id: str) -> List[Shipment]:
    return await Shipment.find(Shipment.OrderID == order_id).to_list()


async def get_shipments_by_shipper(shipper_id: str) -> List[Shipment]:
    return await Shipment.find(Shipment.ShipperID == shipper_id).to_list()


async def update_shipment(
    shipment_id: str, shipment_data: ShipmentUpdate
) -> Optional[Shipment]:
    shipment = await Shipment.get(shipment_id)
    if not shipment:
        return None

    update_data = shipment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # If value is an Enum (like ShipmentStatus), convert to its value string
        if isinstance(value, _Enum):
            value = value.value

        # If updating nested/ID fields, ensure correct types if needed (keep simple assignment for now)
        setattr(shipment, field, value)

    await shipment.save()
    return shipment


async def delete_shipment(shipment_id: str) -> bool:
    shipment = await Shipment.get(shipment_id)
    if not shipment:
        return False

    await shipment.delete()
    return True


async def get_shipment_stats() -> dict:
    total_shipments = await Shipment.all().count()
    pending = await Shipment.find(
        Shipment.Status == ShipmentStatus.PENDING.value
    ).count()

    processing = await Shipment.find(
        Shipment.Status == ShipmentStatus.PROCESSING.value
    ).count()

    shipped = await Shipment.find(
        Shipment.Status == ShipmentStatus.SHIPPED.value
    ).count()

    delivered = await Shipment.find(
        Shipment.Status == ShipmentStatus.DELIVERED.value
    ).count()

    return {
        "TotalShipments": total_shipments,
        "Pending": pending,
        "Processing": processing,
        "Shipped": shipped,
        "Delivered": delivered,
    }


# Get all shipments with shipper details
async def get_all_shipments_with_details():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "accounts",
                    "localField": "ShipperID",
                    "foreignField": "_id",
                    "as": "shipper",
                }
            },
            {"$unwind": {"path": "$shipper", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "ShipmentID": {"$toString": "$_id"},
                    "TrackingNumber": 1,
                    "OrderID": {"$toString": "$OrderID"},
                    "EstimatedDeliveryDate": 1,
                    "ActualDeliveryDate": 1,
                    "Status": 1,
                    "ShipperName": "$shipper.profile.fullName",
                    "_id": 0,
                }
            },
        ]

        raw_data = (
            await Shipment.get_motor_collection()
            .aggregate(pipeline)
            .to_list(length=None)
        )
        return raw_data
    except Exception as e:
        print(f"Error in get_all_shipments_with_details: {str(e)}")
        raise
