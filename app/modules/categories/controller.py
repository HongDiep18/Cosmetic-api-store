from __future__ import annotations
from typing import List, Optional, Tuple

from bson import ObjectId

from app.modules.categories.model import Category
from app.modules.products.model import Product
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


async def list_categories(page: int = 1, limit: int = 50) -> Tuple[List[Category], int]:
    page = max(page, 1)
    limit = max(limit, 1)
    query = Category.find_all()
    total = await query.count()
    items = (
        await query.sort("CreatedAt").skip((page - 1) * limit).limit(limit).to_list()
    )
    return items, total


async def create_category(data: CategoryCreate) -> Category:
    category_data = data.model_dump()
    category = Category(**category_data)
    await category.insert()
    return category


async def get_category(category_id: str) -> Optional[Category]:
    # Tìm theo _id ObjectId
    try:
        if ObjectId.is_valid(category_id):
            category = await Category.get(ObjectId(category_id))
            return category
    except Exception:
        pass
    return None


async def update_category(category_id: str, data: CategoryUpdate) -> Optional[Category]:
    # Tìm theo _id ObjectId
    try:
        if ObjectId.is_valid(category_id):
            category = await Category.get(ObjectId(category_id))
            if category:
                update_data = data.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(category, key, value)
                await category.save()
                return category
    except Exception:
        pass
    return None


async def delete_category(category_id: str) -> bool:
    # Tìm theo _id ObjectId
    try:
        if ObjectId.is_valid(category_id):
            category = await Category.get(ObjectId(category_id))
            if category:
                await category.delete()
                return True
    except Exception:
        pass
    return False


async def list_products_by_category(categoryId: str) -> List[Product]:
    from bson import ObjectId
    if ObjectId.is_valid(categoryId):
        return (
            await Product.find_many(Product.category.categoryId == ObjectId(categoryId))
            .sort("createdAt")
            .to_list()
        )
    return []
