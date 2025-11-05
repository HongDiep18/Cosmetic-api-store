from beanie import init_beanie as beanie_init
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.modules.users.model import User
from app.modules.products.model import Product
from app.modules.orders.model import Order
from app.modules.categories.model import Category
from app.modules.reviews.model import Review
from app.modules.auth.model import Role, Account
from app.modules.shippers.model import Shipper
from app.modules.shipments.model import Shipment
from app.modules.brands.model import Brand

async def init_db() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    await beanie_init(
        database=db,
        document_models=[
            User,
            Product,
            Order,
            Category,
            Brand,
            Review,
            Role,
            Account,
            Shipper,
            Shipment
        ],
    )

 

