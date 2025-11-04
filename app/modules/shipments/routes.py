from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.core.deps import get_current_account, require_admin_account
from app.modules.shipments.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentOut,
    ShipmentStatsOut,
    ShipmentListResponse,
)
from app.modules.shipments.controller import (
    create_shipment,
    get_shipment,
    get_shipments_by_order,
    get_shipments_by_shipper,
    update_shipment,
    delete_shipment,
    get_shipment_stats,
    get_all_shipments_with_details,
)
from app.modules.auth.model import Account
from beanie import PydanticObjectId

router = APIRouter()


# get 4 status shipments
@router.get("/stats", response_model=ShipmentStatsOut)
async def get_shipment_stats_endpoint(
    # current_account: Account = Depends(require_admin_account),
):
    stats = await get_shipment_stats()
    return stats


# create shipment
@router.post("", response_model=ShipmentOut)
async def create_shipment_endpoint(
    shipment_data: ShipmentCreate,
    # current_account: Account = Depends(require_admin_account),
):
    try:
        # Convert string IDs to PydanticObjectId before creating shipment
        data = shipment_data.model_dump()

        try:
            data["OrderID"] = PydanticObjectId(data["OrderID"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OrderID format. Must be a valid ObjectId",
            )

        try:
            data["ShipperID"] = PydanticObjectId(data["ShipperID"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ShipperID format. Must be a valid ObjectId",
            )

        shipment = await create_shipment(data)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create shipment",
            )

        return ShipmentOut.model_validate(shipment, from_attributes=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating shipment: {str(e)}",
        )


# get list all shipments with details
@router.get("/list-all", response_model=list[ShipmentListResponse])
async def list_all_shipments(
    # current_account: Account = Depends(require_admin_account),
):
    try:
        shipments = await get_all_shipments_with_details()
        if not shipments:
            return []
        return shipments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching shipments: {str(e)}",
        )


# get id to view
@router.get("/{shipment_id}", response_model=ShipmentOut)
async def get_shipment_endpoint(shipment_id: str, request: Request):
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


# edit
@router.patch("/{shipment_id}", response_model=ShipmentOut)
async def update_shipment_endpoint(
    shipment_id: str,
    shipment_data: ShipmentUpdate,
    # current_account: Account = Depends(get_current_account),
):
    shipment = await update_shipment(shipment_id, shipment_data)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found"
        )
    return ShipmentOut.model_validate(shipment, from_attributes=True)


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment_endpoint(
    shipment_id: str, current_account: Account = Depends(require_admin_account)
):
    success = await delete_shipment(shipment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found"
        )
    return None
