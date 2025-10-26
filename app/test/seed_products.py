"""
Script to seed products data into MongoDB
Run: python -m app.test.seed_products
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.modules.products.model import Product
from app.core.config import settings


# Mock products data
MOCK_PRODUCTS = [
    {
        "ProductID": "1",
        "ProductName": "Kem chống nắng SPF 50+ Innisfree",
        "Description": "Kem chống nắng vật lý SPF 50+ PA+++ với thành phần tự nhiên từ trà xanh, bảo vệ da khỏi tia UV hiệu quả, không gây bít tắc lỗ chân lông",
        "Price": 299000,
        "OriginalPrice": 399000,
        "Image": "http://localhost:8080/static/images/products/srm-cerave.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "Innisfree",
        "Stock": 50,
        "Rating": 4.5,
        "ReviewCount": 128,
        "IsFeatured": True,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 15, 10, 30),
    },
    {
        "ProductID": "2",
        "ProductName": "Son môi màu đỏ cam Laneige",
        "Description": "Son môi lì màu đỏ cam sang trọng, độ bền màu cao, không khô môi, phù hợp mọi tông da",
        "Price": 599000,
        "OriginalPrice": 799000,
        "Image": "http://localhost:8080/static/images/products/laneige-lipstick.jpg",
        "CategoryID": "2",
        "CategoryName": "Trang điểm",
        "Brand": "Laneige",
        "Stock": 30,
        "Rating": 4.8,
        "ReviewCount": 256,
        "IsFeatured": True,
        "IsNew": True,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 10),
        "UpdatedAt": datetime(2024, 1, 20, 14, 20),
    },
    {
        "ProductID": "3",
        "ProductName": "Serum Vitamin C The Ordinary",
        "Description": "Serum Vitamin C 23% + HA Spheres 2%, làm sáng da, giảm thâm nám, cải thiện kết cấu da",
        "Price": 1299000,
        "Image": "http://localhost:8080/static/images/products/ordinary-serum.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "The Ordinary",
        "Stock": 15,
        "Rating": 4.9,
        "ReviewCount": 89,
        "IsFeatured": True,
        "IsNew": True,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 5),
        "UpdatedAt": datetime(2024, 1, 18, 9, 15),
    },
    {
        "ProductID": "4",
        "ProductName": "Kem dưỡng ẩm Neutrogena",
        "Description": "Kem dưỡng ẩm cho da dầu, không gây bít tắc lỗ chân lông, cung cấp độ ẩm suốt 24h",
        "Price": 499000,
        "OriginalPrice": 699000,
        "Image": "http://localhost:8080/static/images/products/neutrogena-moisturizer.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "Neutrogena",
        "Stock": 40,
        "Rating": 4.6,
        "ReviewCount": 167,
        "IsFeatured": False,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 2),
        "UpdatedAt": datetime(2024, 1, 12, 16, 45),
    },
    {
        "ProductID": "5",
        "ProductName": "Phấn nền Fenty Beauty",
        "Description": "Phấn nền full coverage với 50 tông màu đa dạng, độ bền cao, không gây dị ứng",
        "Price": 899000,
        "Image": "http://localhost:8080/static/images/products/fenty-foundation.jpg",
        "CategoryID": "2",
        "CategoryName": "Trang điểm",
        "Brand": "Fenty Beauty",
        "Stock": 20,
        "Rating": 4.7,
        "ReviewCount": 94,
        "IsFeatured": False,
        "IsNew": True,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 8),
        "UpdatedAt": datetime(2024, 1, 22, 11, 30),
    },
    {
        "ProductID": "6",
        "ProductName": "Toner cân bằng pH Cosrx",
        "Description": "Toner cân bằng pH da với BHA, làm sạch sâu, thu nhỏ lỗ chân lông, ngăn ngừa mụn",
        "Price": 2499000,
        "OriginalPrice": 2999000,
        "Image": "http://localhost:8080/static/images/products/cosrx-toner.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "Cosrx",
        "Stock": 25,
        "Rating": 4.8,
        "ReviewCount": 312,
        "IsFeatured": True,
        "IsNew": True,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 12),
        "UpdatedAt": datetime(2024, 1, 25, 8, 20),
    },
    {
        "ProductID": "7",
        "ProductName": "Mascara làm cong mi Maybelline",
        "Description": "Mascara làm cong mi tự nhiên, không bị vón cục, độ bền cao suốt cả ngày",
        "Price": 699000,
        "Image": "http://localhost:8080/static/images/products/maybelline-mascara.jpg",
        "CategoryID": "2",
        "CategoryName": "Trang điểm",
        "Brand": "Maybelline",
        "Stock": 35,
        "Rating": 4.5,
        "ReviewCount": 143,
        "IsFeatured": False,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 3),
        "UpdatedAt": datetime(2024, 1, 14, 13, 15),
    },
    {
        "ProductID": "8",
        "ProductName": "Kem mắt chống lão hóa Olay",
        "Description": "Kem mắt chống lão hóa với Retinol, giảm nếp nhăn, làm mờ quầng thâm, cải thiện độ đàn hồi",
        "Price": 399000,
        "OriginalPrice": 599000,
        "Image": "http://localhost:8080/static/images/products/olay-eye-cream.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "Olay",
        "Stock": 60,
        "Rating": 4.4,
        "ReviewCount": 78,
        "IsFeatured": False,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 16, 10, 0),
    },
    {
        "ProductID": "9",
        "ProductName": "Son dưỡng môi Vaseline",
        "Description": "Son dưỡng môi Vaseline với vitamin E, làm mềm môi, chống nứt nẻ, hương dâu thơm ngon",
        "Price": 89000,
        "Image": "http://localhost:8080/static/images/products/vaseline-lip-balm.jpg",
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Brand": "Vaseline",
        "Stock": 100,
        "Rating": 4.3,
        "ReviewCount": 245,
        "IsFeatured": False,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 10, 15, 30),
    },
    {
        "ProductID": "10",
        "ProductName": "Kem che khuyết điểm NARS",
        "Description": "Kem che khuyết điểm full coverage, che phủ hoàn hảo mụn, thâm, không gây bít tắc",
        "Price": 1199000,
        "Image": "http://localhost:8080/static/images/products/nars-concealer.jpg",
        "CategoryID": "2",
        "CategoryName": "Trang điểm",
        "Brand": "NARS",
        "Stock": 18,
        "Rating": 4.9,
        "ReviewCount": 156,
        "IsFeatured": True,
        "IsNew": False,
        "Status": "Available",
        "CreatedAt": datetime(2024, 1, 6),
        "UpdatedAt": datetime(2024, 1, 19, 12, 45),
    },
]


async def seed_products():
    """Seed products into MongoDB"""
    print("🌱 Starting product seeding...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[Product])
    
    # Clear existing products (optional)
    print("🗑️  Clearing existing products...")
    await Product.delete_all()
    
    # Insert products
    print("📝 Inserting products...")
    for prod_data in MOCK_PRODUCTS:
        product = Product(**prod_data)
        await product.insert()
        print(f"✅ Inserted: {product.ProductName} - {product.Brand} ({product.CategoryName})")
    
    print(f"\n✨ Successfully seeded {len(MOCK_PRODUCTS)} products!")
    
    # Verify
    total = await Product.find_all().count()
    print(f"📊 Total products in database: {total}")
    
    # Show category breakdown
    print("\n📊 Products by category:")
    for category_name in ["Chăm sóc da", "Trang điểm"]:
        count = await Product.find(Product.CategoryName == category_name).count()
        print(f"  - {category_name}: {count} products")


if __name__ == "__main__":
    asyncio.run(seed_products())

