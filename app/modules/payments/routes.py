from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_account, require_admin_account
from app.modules.payments.schemas import PaymentCreate, PaymentUpdate, PaymentOut
from app.modules.payments.controller import (
    create_payment,
    get_payment,
    get_payments_by_order,
    update_payment,
    delete_payment,
)
from app.modules.auth.model import Account

router = APIRouter(prefix="/api")


@router.post("/payments", response_model=PaymentOut)
async def create_payment_endpoint(
    payment_data: PaymentCreate, current_account: Account = Depends(get_current_account)
):
    payment = await create_payment(payment_data)
    return PaymentOut.model_validate(payment, from_attributes=True)


@router.get("/payments/{payment_id}", response_model=PaymentOut)
async def get_payment_endpoint(
    payment_id: str, current_account: Account = Depends(get_current_account)
):
    payment = await get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return PaymentOut.model_validate(payment, from_attributes=True)


@router.get("/orders/{order_id}/payments", response_model=list[PaymentOut])
async def get_order_payments(
    order_id: str, current_account: Account = Depends(get_current_account)
):
    payments = await get_payments_by_order(order_id)
    return [PaymentOut.model_validate(p, from_attributes=True) for p in payments]


@router.patch("/payments/{payment_id}", response_model=PaymentOut)
async def update_payment_endpoint(
    payment_id: str,
    payment_data: PaymentUpdate,
    current_account: Account = Depends(require_admin_account),
):
    payment = await update_payment(payment_id, payment_data)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return PaymentOut.model_validate(payment, from_attributes=True)


@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_endpoint(
    payment_id: str, current_account: Account = Depends(require_admin_account)
):
    success = await delete_payment(payment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return None
