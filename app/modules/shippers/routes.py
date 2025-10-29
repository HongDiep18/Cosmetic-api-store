from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_admin_account
from app.modules.shippers.schemas import ShipperCreate, ShipperOut, ShipperUpdate
from app.modules.shippers.controller import (
    create_shipper,
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
    # _: str = Depends(require_admin_account),
):
    shipper = await create_shipper(data)
    return ShipperOut.model_validate(shipper, from_attributes=True)


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


@router.get("/{shipper_id}", response_model=ShipperOut)
async def get_shipper_endpoint(
    shipper_id: str,
    _: str = Depends(require_admin_account),
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
    _: str = Depends(require_admin_account),
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
    _: str = Depends(require_admin_account),
):
    success = await delete_shipper(shipper_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipper not found"
        )
    return None
