"""
Script to seed categories data into MongoDB
Run: python -m app.test.seed_categories
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.modules.categories.model import Category
from app.core.config import settings


# Mock categories data
MOCK_CATEGORIES = [
    {
        "CategoryID": "1",
        "CategoryName": "Chăm sóc da",
        "Description": "Các sản phẩm chăm sóc da mặt và cơ thể",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 1),
    },
    {
        "CategoryID": "2",
        "CategoryName": "Trang điểm",
        "Description": "Các sản phẩm trang điểm cho khuôn mặt",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 1),
    },
    {
        "CategoryID": "3",
        "CategoryName": "Chăm sóc tóc",
        "Description": "Dầu gội, dầu xả và các sản phẩm chăm sóc tóc",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 1),
    },
    {
        "CategoryID": "4",
        "CategoryName": "Chăm sóc cơ thể",
        "Description": "Sữa tắm, kem dưỡng thể và các sản phẩm chăm sóc cơ thể",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 1),
    },
    {
        "CategoryID": "5",
        "CategoryName": "Nước hoa",
        "Description": "Nước hoa nam, nữ và unisex",
        "CreatedAt": datetime(2024, 1, 1),
        "UpdatedAt": datetime(2024, 1, 1),
    },
]


async def seed_categories():
    """Seed categories into MongoDB"""
    print("🌱 Starting category seeding...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[Category])
    
    # Clear existing categories (optional)
    print("🗑️  Clearing existing categories...")
    await Category.delete_all()
    
    # Insert categories
    print("📝 Inserting categories...")
    for cat_data in MOCK_CATEGORIES:
        category = Category(**cat_data)
        await category.insert()
        print(f"✅ Inserted: {category.CategoryName} (ID: {category.CategoryID})")
    
    print(f"\n✨ Successfully seeded {len(MOCK_CATEGORIES)} categories!")
    
    # Verify
    total = await Category.find_all().count()
    print(f"📊 Total categories in database: {total}")


if __name__ == "__main__":
    asyncio.run(seed_categories())

