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
    DeliveryStatusUpdate,
)
from app.modules.shippers.deliveries import (
    get_delivery_details,
    list_deliveries_by_shipper,
)
from app.modules.shippers.controller import (
    create_account_shipper,
    get_shipper,
    list_shippers,
    update_shipper,
    delete_shipper,
)

from app.core.deps import require_admin_account
from app.modules.orders.controller import update_order_status
from beanie import PydanticObjectId

router = APIRouter()


# create shipper - removed, use create_shipper_account instead


@router.post("", response_model=ShipperOut, status_code=status.HTTP_201_CREATED)
async def create_shipper_account(
    data: ShipperCreate,
):
    print("📩 Dữ liệu nhận được:", data.model_dump())
    try:
        # Gọi controller tạo tài khoản
        account_dict = await create_account_shipper(data)
        # Validate output schema
        validated_shipper = ShipperOut.model_validate(account_dict)
        return validated_shipper

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
        return [ShipperOut.model_validate(s.model_dump()) for s in shippers]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shippers: {str(e)}",
        )


# Get list of all deliveries for shipper - PHẢI ĐẶT TRƯỚC /{shipper_id}
@router.get("/deliveries", response_model=list[DeliverySummaryOut])
async def get_deliveries_list(
    status: Optional[str] = None,
):
    """
    Lấy danh sách vận đơn - TEST MODE (không  xác thực)
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


# Update delivery/order status - MUST be placed BEFORE /{shipper_id} route
@router.patch("/deliveries/{order_id}/status")
async def update_delivery_status_endpoint(
    order_id: str,
    status_update: DeliveryStatusUpdate,
    # _: str = Depends(require_shipper_account),
):
    """
    Update delivery/order status from shipper portal.

    This endpoint updates the order status in the orders collection.
    The order_id can be either the OrderID or ShipmentID (which will be resolved to OrderID).

    Valid status values:
    - Processing
    - Shipped
    - Delivered
    - Failed
    - Cancelled
    """
    try:
        new_status = status_update.status.strip()

        # Validate status is one of the allowed values
        allowed_statuses = [
            "Pending",
            "Confirmed",
            "Processing",
            "Shipped",
            "Delivered",
            "Failed",
            "Cancelled",
        ]
        if new_status not in allowed_statuses:
            # Try to match case-insensitively
            new_status_lower = new_status.lower()
            for allowed in allowed_statuses:
                if allowed.lower() == new_status_lower:
                    new_status = allowed
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}",
                )

        # Try to update the order
        # First, try to use order_id as OrderID (MongoDB _id)
        order = None
        try:
            # Validate that order_id is a valid ObjectId format
            try:
                PydanticObjectId(order_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid order ID format: {order_id}",
                )

            order = await update_order_status(order_id, new_status)
            if order:
                return {
                    "success": True,
                    "OrderID": str(order.id),
                    "Status": order.Status,
                    "UpdatedAt": order.UpdatedAt,
                }
        except HTTPException:
            raise
        except Exception as e:
            print(f"⚠️ Failed to update order with ID {order_id}: {e}")
            import traceback

            traceback.print_exc()

        # If that fails, try to find order by ShipmentID
        # Import here to avoid circular dependency
        from app.modules.shipments.model import Shipment

        try:
            shipment = await Shipment.get(PydanticObjectId(order_id))
            if shipment and shipment.OrderID:
                order = await update_order_status(str(shipment.OrderID), new_status)
                if order:
                    return {
                        "success": True,
                        "OrderID": str(order.id),
                        "Status": order.Status,
                        "UpdatedAt": order.UpdatedAt,
                    }
        except Exception as e:
            print(f"⚠️ Failed to find shipment with ID {order_id}: {e}")

        # If we get here, order was not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found: {order_id}. Please verify the order ID is correct.",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating delivery status: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating delivery status: {str(e)}",
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
    return ShipperOut.model_validate(shipper.model_dump())


@router.patch("/{shipper_id}", response_model=ShipperOut)
async def update_shipper_endpoint(
    shipper_id: str,
    data: ShipperUpdate,
    # _: str = Depends(require_shipper_account),
    _: str = Depends(require_admin_account),  # Chỉ cho phép admin chỉnh sử
):
    shipper = await update_shipper(shipper_id, data)
    if not shipper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipper not found"
        )
    return ShipperOut.model_validate(shipper.model_dump())


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
