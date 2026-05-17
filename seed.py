"""
Seed script — populates the database with sample data.

Run inside the API container:
    docker exec -it cosmetic_api python seed.py

Or locally (activate venv first):
    python seed.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.security import get_passwordHash
from app.modules.auth.model import Role, Account
from app.modules.users.model import User
from app.modules.shippers.model import Shipper
from app.modules.categories.model import Category
from app.modules.brands.model import Brand
from app.modules.products.model import Product
from app.modules.orders.model import Order, OrderItem
from app.modules.payments.model import Payment
from app.modules.shipments.model import Shipment
from app.modules.reviews.model import Review
from app.modules.orders.schemas import OrderStatus
from app.modules.shipments.schemas import ShipmentStatus


async def seed() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]

    await init_beanie(
        database=db,
        document_models=[
            Role,
            Account,
            User,
            Shipper,
            Category,
            Brand,
            Product,
            Order,
            Payment,
            Shipment,
            Review,
        ],
    )

    # ── Clear existing data (safe to re-run) ─────────────────────────────────
    print("Clearing existing data...")
    for model in [
        Review,
        Shipment,
        Payment,
        Order,
        Product,
        Brand,
        Category,
        Shipper,
        User,
        Account,
        Role,
    ]:
        await model.find_all().delete()

    # ── Roles (3) ─────────────────────────────────────────────────────────────
    role_user = await Role(RoleName="User").insert()
    role_admin = await Role(RoleName="Admin").insert()
    role_shipper = await Role(RoleName="Shipper").insert()
    print("Roles created (3)")

    # ── Accounts (5: 1 admin, 2 users, 2 shippers) ───────────────────────────
    acc_admin = await Account(
        Email="admin@cosmetic.com",
        PasswordHash=get_passwordHash("Admin123!"),
        RoleID=role_admin.id,
        Status="Active",
    ).insert()
    acc_user1 = await Account(
        Email="user1@cosmetic.com",
        PasswordHash=get_passwordHash("User123!"),
        RoleID=role_user.id,
        Status="Active",
    ).insert()
    acc_user2 = await Account(
        Email="user2@cosmetic.com",
        PasswordHash=get_passwordHash("User123!"),
        RoleID=role_user.id,
        Status="Active",
    ).insert()
    acc_shipper1 = await Account(
        Email="shipper1@cosmetic.com",
        PasswordHash=get_passwordHash("Shipper123!"),
        RoleID=role_shipper.id,
        Status="Active",
    ).insert()
    acc_shipper2 = await Account(
        Email="shipper2@cosmetic.com",
        PasswordHash=get_passwordHash("Shipper123!"),
        RoleID=role_shipper.id,
        Status="Active",
    ).insert()
    print("Accounts created (5)")

    # ── Users (3) ─────────────────────────────────────────────────────────────
    user1 = await User(
        AccountID=acc_user1.id,
        FullName="Nguyen Thi Lan",
        Phone="0912345678",
        Address="456 Tran Hung Dao, Quan 5, TP.HCM",
    ).insert()
    user2 = await User(
        AccountID=acc_user2.id,
        FullName="Tran Van Minh",
        Phone="0923456789",
        Address="789 Le Van Sy, Quan 3, TP.HCM",
    ).insert()
    user3 = await User(
        AccountID=acc_admin.id,
        FullName="Admin Manager",
        Phone="0901234567",
        Address="123 Nguyen Hue, Quan 1, TP.HCM",
    ).insert()
    print("Users created (3)")

    # ── Shippers (3) ──────────────────────────────────────────────────────────
    shipper1 = await Shipper(
        AccountID=acc_shipper1.id, FullName="Le Van Cuong", Phone="0934567890"
    ).insert()
    shipper2 = await Shipper(
        AccountID=acc_shipper2.id, FullName="Pham Thi Hoa", Phone="0945678901"
    ).insert()
    shipper3 = await Shipper(
        AccountID=None, FullName="Vo Thanh Tung", Phone="0956789012"
    ).insert()
    print("Shippers created (3)")

    # ── Categories (4) ────────────────────────────────────────────────────────
    cat_skin = await Category(
        CategoryName="Skincare", Description="Face and body skincare products"
    ).insert()
    cat_makeup = await Category(
        CategoryName="Makeup", Description="Cosmetics and makeup products"
    ).insert()
    cat_hair = await Category(
        CategoryName="Hair Care", Description="Shampoo, conditioner and hair treatments"
    ).insert()
    cat_fragrance = await Category(
        CategoryName="Fragrance", Description="Perfumes and body mists"
    ).insert()
    print("Categories created (4)")

    # ── Brands (3) ────────────────────────────────────────────────────────────
    brand_laneige = await Brand(BrandName="Laneige").insert()
    brand_loreal = await Brand(BrandName="L'Oreal").insert()
    brand_innisfree = await Brand(BrandName="Innisfree").insert()
    print("Brands created (3)")

    # ── Products (15) ─────────────────────────────────────────────────────────
    # (name, desc, price, stock, category, brand, rating, featured, is_new, orig_price)
    products_data = [
        # Skincare — Laneige (3)
        (
            "Laneige Water Sleeping Mask",
            "Overnight hydrating mask that replenishes moisture while you sleep.",
            650_000,
            50,
            cat_skin,
            "Laneige",
            4.8,
            True,
            False,
            720_000,
        ),
        (
            "Laneige Lip Sleeping Mask",
            "Nourishing overnight lip mask with sweet vitamin complex.",
            380_000,
            80,
            cat_skin,
            "Laneige",
            4.7,
            True,
            False,
            420_000,
        ),
        (
            "Laneige Cream Skin Toner",
            "Toner with milk filtrate and white leaf tea water for smooth skin.",
            520_000,
            60,
            cat_skin,
            "Laneige",
            4.6,
            False,
            True,
            None,
        ),
        # Skincare — Innisfree (3)
        (
            "Innisfree Green Tea Seed Serum",
            "Jeju green tea seed serum for all-day hydration.",
            490_000,
            70,
            cat_skin,
            "Innisfree",
            4.5,
            False,
            False,
            550_000,
        ),
        (
            "Innisfree Volcanic Pore Clay Mask",
            "Removes excess sebum and impurities with Jeju volcanic clusters.",
            280_000,
            100,
            cat_skin,
            "Innisfree",
            4.4,
            False,
            False,
            320_000,
        ),
        (
            "Innisfree Cherry Blossom Jelly Cream",
            "Light jelly cream that blooms moisturization on skin.",
            390_000,
            75,
            cat_skin,
            "Innisfree",
            4.5,
            False,
            True,
            None,
        ),
        # Skincare — L'Oreal (1)
        (
            "L'Oreal Hyaluronic Acid Serum 1.5%",
            "Intense hydration serum with 1.5% hyaluronic acid.",
            420_000,
            90,
            cat_skin,
            "L'Oreal",
            4.3,
            True,
            False,
            480_000,
        ),
        # Makeup — L'Oreal (3)
        (
            "L'Oreal True Match Foundation",
            "Blendable foundation that matches your exact skin tone.",
            320_000,
            120,
            cat_makeup,
            "L'Oreal",
            4.2,
            False,
            False,
            360_000,
        ),
        (
            "L'Oreal Voluminous Mascara",
            "Original mascara for 5x the volume in one coat.",
            210_000,
            150,
            cat_makeup,
            "L'Oreal",
            4.5,
            True,
            False,
            None,
        ),
        (
            "L'Oreal Color Riche Lipstick",
            "Moisturizing lipstick with intense colour.",
            190_000,
            200,
            cat_makeup,
            "L'Oreal",
            4.3,
            False,
            True,
            None,
        ),
        # Makeup — Laneige & Innisfree (2)
        (
            "Laneige Neo Cushion Glow",
            "Glass skin effect cushion foundation with dewy finish.",
            580_000,
            65,
            cat_makeup,
            "Laneige",
            4.6,
            True,
            True,
            650_000,
        ),
        (
            "Innisfree My Cushion Foundation",
            "Air-light cushion foundation with SPF50+ PA++++.",
            350_000,
            80,
            cat_makeup,
            "Innisfree",
            4.4,
            False,
            False,
            400_000,
        ),
        # Hair Care — L'Oreal (3)
        (
            "L'Oreal Elvive Extraordinary Oil Shampoo",
            "Enriched with 6 precious oils for silky hair.",
            185_000,
            180,
            cat_hair,
            "L'Oreal",
            4.2,
            False,
            False,
            210_000,
        ),
        (
            "L'Oreal Elvive Total Repair 5 Conditioner",
            "Repairs 5 signs of damaged hair.",
            175_000,
            160,
            cat_hair,
            "L'Oreal",
            4.1,
            False,
            False,
            None,
        ),
        (
            "L'Oreal Color Vibrancy Shampoo",
            "Protects and prolongs colour-treated hair vibrancy.",
            195_000,
            140,
            cat_hair,
            "L'Oreal",
            4.0,
            False,
            True,
            None,
        ),
    ]

    p = []
    for (
        name,
        desc,
        price,
        stock,
        cat,
        brand,
        rating,
        featured,
        is_new,
        orig,
    ) in products_data:
        prod = await Product(
            ProductName=name,
            Description=desc,
            Price=price,
            Stock=stock,
            CategoryID=str(cat.id),
            CategoryName=cat.CategoryName,
            Brand=brand,
            Rating=rating,
            ReviewCount=0,
            IsFeatured=featured,
            IsNew=is_new,
            OriginalPrice=orig,
        ).insert()
        p.append(prod)
    print(f"Products created ({len(p)})")

    # ── Orders (3) ────────────────────────────────────────────────────────────
    now = datetime.utcnow()

    order1 = await Order(
        UserID=user1.id,
        ShippingAddress="456 Tran Hung Dao, Quan 5, TP.HCM",
        TotalAmount=p[0].Price + p[1].Price,
        Status=OrderStatus.DELIVERED,
        Items=[
            OrderItem(ProductID=p[0].id, Quantity=1, Price=p[0].Price),
            OrderItem(ProductID=p[1].id, Quantity=1, Price=p[1].Price),
        ],
        OrderDate=now - timedelta(days=10),
        CreatedAt=now - timedelta(days=10),
        UpdatedAt=now - timedelta(days=2),
    ).insert()

    order2 = await Order(
        UserID=user2.id,
        ShippingAddress="789 Le Van Sy, Quan 3, TP.HCM",
        TotalAmount=p[3].Price + p[9].Price + p[12].Price,
        Status=OrderStatus.SHIPPED,
        Items=[
            OrderItem(ProductID=p[3].id, Quantity=1, Price=p[3].Price),
            OrderItem(ProductID=p[9].id, Quantity=1, Price=p[9].Price),
            OrderItem(ProductID=p[12].id, Quantity=1, Price=p[12].Price),
        ],
        OrderDate=now - timedelta(days=5),
        CreatedAt=now - timedelta(days=5),
        UpdatedAt=now - timedelta(days=1),
    ).insert()

    order3 = await Order(
        UserID=user1.id,
        ShippingAddress="456 Tran Hung Dao, Quan 5, TP.HCM",
        TotalAmount=p[5].Price * 2 + p[7].Price,
        Status=OrderStatus.PENDING,
        Items=[
            OrderItem(ProductID=p[5].id, Quantity=2, Price=p[5].Price),
            OrderItem(ProductID=p[7].id, Quantity=1, Price=p[7].Price),
        ],
        OrderDate=now - timedelta(days=1),
        CreatedAt=now - timedelta(days=1),
        UpdatedAt=now - timedelta(days=1),
    ).insert()
    print("Orders created (3)")

    # ── Payments (3) ──────────────────────────────────────────────────────────
    await Payment(
        OrderID=order1.id,
        PaymentMethod="Credit Card",
        Amount=order1.TotalAmount,
        Status="Paid",
        PaymentDate=now - timedelta(days=10),
    ).insert()
    await Payment(
        OrderID=order2.id,
        PaymentMethod="Bank Transfer",
        Amount=order2.TotalAmount,
        Status="Paid",
        PaymentDate=now - timedelta(days=5),
    ).insert()
    await Payment(
        OrderID=order3.id,
        PaymentMethod="Cash on Delivery",
        Amount=order3.TotalAmount,
        Status="Pending",
        PaymentDate=None,
    ).insert()
    print("Payments created (3)")

    # ── Shipments (3) ─────────────────────────────────────────────────────────
    await Shipment(
        OrderID=order1.id,
        ShipperID=shipper1.id,
        TrackingNumber="TRK-2026-001",
        Status=ShipmentStatus.DELIVERED,
        ShipmentDate=now - timedelta(days=9),
        EstimatedDeliveryDate=now - timedelta(days=7),
        ActualDeliveryDate=now - timedelta(days=2),
    ).insert()
    await Shipment(
        OrderID=order2.id,
        ShipperID=shipper2.id,
        TrackingNumber="TRK-2026-002",
        Status=ShipmentStatus.SHIPPED,
        ShipmentDate=now - timedelta(days=4),
        EstimatedDeliveryDate=now + timedelta(days=1),
        ActualDeliveryDate=None,
    ).insert()
    await Shipment(
        OrderID=order3.id,
        ShipperID=shipper1.id,
        TrackingNumber="TRK-2026-003",
        Status=ShipmentStatus.PENDING,
        ShipmentDate=None,
        EstimatedDeliveryDate=now + timedelta(days=3),
        ActualDeliveryDate=None,
    ).insert()
    print("Shipments created (3)")

    # ── Reviews (3) ───────────────────────────────────────────────────────────
    await Review(
        UserID=str(user1.id),
        ProductID=str(p[0].id),
        Rating=5,
        Comment="Amazing sleeping mask! Skin feels so hydrated every morning.",
    ).insert()
    await Review(
        UserID=str(user2.id),
        ProductID=str(p[3].id),
        Rating=4,
        Comment="Great serum, skin feels smooth. Will buy again.",
    ).insert()
    await Review(
        UserID=str(user1.id),
        ProductID=str(p[1].id),
        Rating=5,
        Comment="Best lip mask I have ever tried. Lips are so soft!",
    ).insert()

    # Update review stats on the 3 reviewed products
    await p[0].set({"Rating": 5.0, "ReviewCount": 1})
    await p[3].set({"Rating": 4.0, "ReviewCount": 1})
    await p[1].set({"Rating": 5.0, "ReviewCount": 1})
    print("Reviews created (3)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("Seed completed!")
    print("=" * 50)
    print("Collection      Rows")
    print("-" * 30)
    print("roles              3")
    print("accounts           5")
    print("users              3")
    print("shippers           3")
    print("categories         4")
    print("brands             3")
    print("products          15")
    print("orders             3")
    print("payments           3")
    print("shipments          3")
    print("reviews            3")
    print("=" * 50)
    print("\nLogin credentials:")
    print("  admin@cosmetic.com    / Admin123!")
    print("  user1@cosmetic.com    / User123!")
    print("  user2@cosmetic.com    / User123!")
    print("  shipper1@cosmetic.com / Shipper123!")
    print("  shipper2@cosmetic.com / Shipper123!")


if __name__ == "__main__":
    asyncio.run(seed())
