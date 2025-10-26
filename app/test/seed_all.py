"""
Script to seed all data (categories and products) into MongoDB
Run: python -m app.test.seed_all
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.modules.categories.model import Category
from app.modules.products.model import Product
from app.core.config import settings

# Import seed data
from app.test.seed_categories import MOCK_CATEGORIES
from app.test.seed_products import MOCK_PRODUCTS
from app.test.download_placeholder_images import download_images


async def seed_all():
    """Seed all data into MongoDB"""
    print("=" * 60)
    print("🌱 SEEDING ALL DATA INTO MONGODB")
    print("=" * 60)
    
    # Download placeholder images first
    print("\n" + "=" * 60)
    print("📥 STEP 0: DOWNLOADING PLACEHOLDER IMAGES")
    print("=" * 60)
    download_images()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    # Initialize Beanie with all models
    await init_beanie(
        database=db,
        document_models=[Category, Product]
    )
    
    # 1. Seed Categories
    print("\n" + "=" * 60)
    print("📁 SEEDING CATEGORIES")
    print("=" * 60)
    await Category.delete_all()
    for cat_data in MOCK_CATEGORIES:
        category = Category(**cat_data)
        await category.insert()
        print(f"✅ {category.CategoryName}")
    
    total_categories = await Category.find_all().count()
    print(f"\n✨ Seeded {total_categories} categories")
    
    # 2. Seed Products
    print("\n" + "=" * 60)
    print("📦 SEEDING PRODUCTS")
    print("=" * 60)
    await Product.delete_all()
    for prod_data in MOCK_PRODUCTS:
        product = Product(**prod_data)
        await product.insert()
        print(f"✅ {product.ProductName} - {product.Brand} ({product.CategoryName})")
    
    total_products = await Product.find_all().count()
    print(f"\n✨ Seeded {total_products} products")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Categories: {total_categories}")
    print(f"✅ Products: {total_products}")
    
    # Breakdown by category
    print("\n📊 Products by category:")
    for category in MOCK_CATEGORIES:
        count = await Product.find(Product.CategoryName == category["CategoryName"]).count()
        print(f"  - {category['CategoryName']}: {count} products")
    
    print("\n" + "=" * 60)
    print("✨ ALL DATA SEEDED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_all())

