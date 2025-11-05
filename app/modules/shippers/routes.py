from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import traceback
from app.modules.shippers.deps import require_shipper_account
from app.modules.shippers.schemas import (
    ShipperCreate,
    ShipperOut,
    ShipperUpdate,
    DeliveryDetailsOut,
    DeliverySummaryOut,
)
from app.modules.shippers.deliveries import get_delivery_details
from app.modules.shippers.controllers.list_deliveries import list_deliveries_by_shipper
from app.modules.shippers.controller import (
    create_shipper,
    create_account_shipper,
    get_shipper,
    list_shippers,
    update_shipper,
    delete_shipper,
)

router = APIRouter()


# create shipper
@router.post("/", response_model=ShipperOut, status_code=status.HTTP_201_CREATED)
async def create_shipper_endpoint(
    data: ShipperCreate,
    # _: str = Depends(require_shipper_account),
):
    shipper = await create_shipper(data)
    return ShipperOut.model_validate(shipper, from_attributes=True)


@router.post(
    "",
    response_model=ShipperOut,
    #  status_code=status.HTTP_201_CREATED
)
async def create_shipper_account(
    data: ShipperCreate,
    # _: str = Depends(require_shipper_account),
):
    print("📩 Dữ liệu nhận được:", data.model_dump())
    try:
        # Gọi controller tạo tài khoản + user
        shipper_dict = await create_account_shipper(data)
        # Validate output schema
        validated_user = ShipperOut.model_validate(shipper_dict)
        return validated_user

    except Exception as e:
        print("❌ ValidationError chi tiết:")
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={
                "error": "Response model validation failed",
                "details": str(e),
            },
        )


# get all shippers
@router.get("/list-shippers", response_model=list[ShipperOut])
async def list_shippers_endpoint():
    try:
        shippers = await list_shippers()
        return [ShipperOut.model_validate(s, from_attributes=True) for s in shippers]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shippers: {str(e)}",
        )


# Get list of all deliveries for shipper - PHẢI ĐẶT TRƯỚC /{shipper_id}
@router.get("/shipper-portal/deliveries", response_model=list[DeliverySummaryOut])
async def get_deliveries_list(
    status: Optional[str] = None,
):
    """
    Lấy danh sách vận đơn - TEST MODE (không cần xác thực)
    """
    try:
        # Test mode: không cần xác thực, lấy tất cả đơn hàng
        shipper_id = None  # None để lấy tất cả đơn hàng (test mode)

        # Gọi controller để lấy danh sách
        deliveries = await list_deliveries_by_shipper(
            shipper_id=shipper_id,  # None sẽ lấy tất cả đơn hàng
            status=status,
        )
        return deliveries
    except Exception as e:
        print(f"❌ Error getting deliveries list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# get delivery details for shipper portal
@router.get("/deliveries/{shipment_id}", response_model=DeliveryDetailsOut)
async def get_delivery_details_endpoint(
    shipment_id: str,
    # _: str = Depends(require_shipper_account),
):
    """
    Get delivery details including:
    - Tracking number and status
    - Customer info (name, phone)
    - Delivery address
    - Order items and total
    - COD amount to collect
    """
    try:
        return await get_delivery_details(
            shipment_id=shipment_id,
            # current_shipper_id=current_shipper,
        )
    except Exception as e:
        print(f"❌ Error getting delivery details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{shipper_id}", response_model=ShipperOut)
async def get_shipper_endpoint(
    shipper_id: str,
    _: str = Depends(require_shipper_account),
):
    shipper = await get_shipper(shipper_id)
    if not shipper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipper not found"
        )
    return ShipperOut.model_validate(shipper, from_attributes=True)


@router.patch("/{shipper_id}", response_model=ShipperOut)
async def update_shipper_endpoint(
    shipper_id: str,
    data: ShipperUpdate,
    _: str = Depends(require_shipper_account),
):
    shipper = await update_shipper(shipper_id, data)
    if not shipper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipper not found"
        )
    return ShipperOut.model_validate(shipper, from_attributes=True)


@router.delete("/{shipper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipper_endpoint(
    shipper_id: str,
    _: str = Depends(require_shipper_account),
):
    success = await delete_shipper(shipper_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipper not found"
        )
    return None
