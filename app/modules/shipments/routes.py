from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_account, require_admin_account
from app.modules.shipments.schemas import ShipmentCreate, ShipmentUpdate, ShipmentOut
from app.modules.shipments.controller import (
    create_shipment,
    get_shipment,
    get_shipments_by_order,
    get_shipments_by_shipper,
    update_shipment,
    delete_shipment,
)
from app.modules.auth.model import Account

router = APIRouter(prefix="/api/v1")


@router.post("/shipments", response_model=ShipmentOut)
async def create_shipment_endpoint(
    shipment_data: ShipmentCreate,
    current_account: Account = Depends(require_admin_account),
):
    shipment = await create_shipment(shipment_data)
    return ShipmentOut.model_validate(shipment, from_attributes=True)


@router.get("/shipments/{shipment_id}", response_model=ShipmentOut)
async def get_shipment_endpoint(
    shipment_id: str, current_account: Account = Depends(get_current_account)
):
    shipment = await get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found"
        )
    return ShipmentOut.model_validate(shipment, from_attributes=True)


@router.get("/orders/{order_id}/shipments", response_model=list[ShipmentOut])
async def get_order_shipments(
    order_id: str, current_account: Account = Depends(get_current_account)
):
    shipments = await get_shipments_by_order(order_id)
    return [ShipmentOut.model_validate(s, from_attributes=True) for s in shipments]


@router.get("/shippers/{shipper_id}/shipments", response_model=list[ShipmentOut])
async def get_shipper_shipments(
    shipper_id: str, current_account: Account = Depends(get_current_account)
):
    shipments = await get_shipments_by_shipper(shipper_id)
    return [ShipmentOut.model_validate(s, from_attributes=True) for s in shipments]


@router.patch("/shipments/{shipment_id}", response_model=ShipmentOut)
async def update_shipment_endpoint(
    shipment_id: str,
    shipment_data: ShipmentUpdate,
    current_account: Account = Depends(require_admin_account),
):
    shipment = await update_shipment(shipment_id, shipment_data)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found"
        )
    return ShipmentOut.model_validate(shipment, from_attributes=True)


@router.delete("/shipments/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment_endpoint(
    shipment_id: str, current_account: Account = Depends(require_admin_account)
):
    success = await delete_shipment(shipment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found"
        )
    return None
