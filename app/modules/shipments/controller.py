from typing import List, Optional

from app.modules.shipments.model import Shipment
from app.modules.shipments.schemas import ShipmentUpdate, ShipmentStatus


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

    # Use Beanie's find(...) query method instead of non-existent filter(...) on the
    # Document class. Compare against the enum values.
    preparing = await Shipment.find(
        Shipment.Status == ShipmentStatus.PREPARING.value
    ).count()

    delivering = await Shipment.find(
        Shipment.Status == ShipmentStatus.IN_TRANSIT.value
    ).count()

    delivered = await Shipment.find(
        Shipment.Status == ShipmentStatus.DELIVERED.value
    ).count()

    # Return keys matching the ShipmentStatsOut schema (PascalCase)
    return {
        "TotalShipments": total_shipments,
        "Preparing": preparing,
        "Delivering": delivering,
        "Delivered": delivered,
    }
