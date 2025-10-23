from __future__ import annotations
from typing import List, Optional

from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schemas import OrderCreate


async def create_order(user_id: str, data: OrderCreate) -> Order:
    items: List[OrderItem] = [
        OrderItem(
            product_id=i.product_id,
            quantity=i.quantity,
            price_at_purchase=i.price_at_purchase,
        )
        for i in data.products
    ]
    total_amount = sum(i.quantity * i.price_at_purchase for i in items)
    order = Order(
        user_id=user_id,
        products=items,
        total_amount=total_amount,
        shipping_address=data.shipping_address,
    )
    await order.insert()
    return order


async def get_user_orders(user_id: str) -> List[Order]:
    return await Order.find(Order.user_id == user_id).sort("-created_at").to_list()


async def list_all_orders() -> List[Order]:
    return await Order.find_all().sort("-created_at").to_list()


async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    order = await Order.get(order_id)
    if not order:
        return None
    order.status = status
    await order.save()
    return order
