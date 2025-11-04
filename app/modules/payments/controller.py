from typing import List, Optional

from app.modules.payments.model import Payment
from app.modules.payments.schemas import PaymentCreate, PaymentUpdate
from app.modules.orders.model import Order
from beanie import Document, PydanticObjectId

# async def create_payment(payment_data: PaymentCreate) -> Payment:
#     payment = Payment(**payment_data.model_dump())
#     await payment.insert()
#     return payment


async def create_payment(payment_data: PaymentCreate) -> Payment:
    order = await Order.get(PydanticObjectId(payment_data.OrderID))
    if not order:
        raise Exception("Order not found")

    if payment_data.Amount != order.TotalAmount:
        raise Exception("Payment amount mismatch")

    payment = Payment(
        OrderID=payment_data.OrderID,
        PaymentMethod= 'Pending'  ,
        Amount=payment_data.Amount,
    )
    await payment.insert()

    return payment

async def get_payment(payment_id: str) -> Optional[Payment]:
    return await Payment.get(payment_id)


async def get_payments_by_order(order_id: str) -> List[Payment]:
    return await Payment.find(Payment.OrderID == order_id).to_list()


async def update_payment(
    payment_id: str, payment_data: PaymentUpdate
) -> Optional[Payment]:
    payment = await Payment.get(payment_id)
    if not payment:
        return None

    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)

    await payment.save()
    return payment


async def delete_payment(payment_id: str) -> bool:
    payment = await Payment.get(payment_id)
    if not payment:
        return False

    await payment.delete()
    return True
