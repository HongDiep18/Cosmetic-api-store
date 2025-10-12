from typing import List, Optional

from app.modules.shipments.model import Shipment
from app.modules.shipments.schemas import ShipmentCreate, ShipmentUpdate


async def create_shipment(shipment_data: ShipmentCreate) -> Shipment:
    shipment = Shipment(**shipment_data.model_dump())
    await shipment.insert()
    return shipment


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
