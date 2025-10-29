from __future__ import annotations
from typing import List, Optional
from app.modules.orders.model import Order, OrderItem
from app.modules.orders.schemas import OrderCreate


async def create_order(user_id: str, data: OrderCreate) -> Order:
    try:
        # Create items list
        items: List[OrderItem] = []
        for item in data.Items:
            items.append(
                OrderItem(
                    ProductID=item.ProductID,  # Use string ID directly
                    Quantity=item.Quantity,
                    Price=item.Price,
                )
            )

        # Calculate total amount
        total_amount = sum(item.Price * item.Quantity for item in items)

        # Create and save order
        order = Order(
            UserID=user_id,  # Use string ID directly
            Items=items,
            TotalAmount=total_amount,
            ShippingAddress=data.ShippingAddress,
        )
        await order.insert()
        return order
    except Exception as e:
        raise Exception(f"Error creating order: {str(e)}")


async def get_user_orders(user_id: str) -> List[Order]:
    try:
        # Find orders with exact user_id string match
        orders = await Order.find({"UserID": user_id}).sort("-CreatedAt").to_list()

        # Ensure each order's _id is converted to string
        for order in orders:
            if hasattr(order, "_id"):
                order._id = str(order._id)

        return orders
    except Exception as e:
        raise Exception(f"Error fetching user orders: {str(e)}")


async def list_all_orders() -> List[Order]:
    return await Order.find_all().sort("-CreatedAt").to_list()


async def update_order_status(order_id: str, status: str) -> Optional[Order]:
    order = await Order.get(order_id)
    if not order:
        return None
    order.Status = status
    await order.save()
    return order
