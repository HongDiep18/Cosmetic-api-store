from app.modules.shippers.model import Shipper
from app.modules.shippers.schemas import ShipperCreate, ShipperUpdate


async def create_shipper(data: ShipperCreate) -> Shipper:
    shipper = Shipper(
        fullName=data.fullName,
        phone=data.phone,
    )
    await shipper.insert()
    return shipper


async def get_shipper(shipper_id: str) -> Shipper | None:
    return await Shipper.get(shipper_id)


async def list_shippers() -> list[Shipper]:
    return await Shipper.find_all().to_list()


async def update_shipper(shipper_id: str, data: ShipperUpdate) -> Shipper | None:
    shipper = await Shipper.get(shipper_id)
    if not shipper:
        return None

    if data.fullName is not None:
        shipper.fullName = data.fullName
    if data.phone is not None:
        shipper.phone = data.phone

    await shipper.save()
    return shipper


async def delete_shipper(shipper_id: str) -> bool:
    shipper = await Shipper.get(shipper_id)
    if not shipper:
        return False

    await shipper.delete()
    return True
