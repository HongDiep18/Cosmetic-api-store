from __future__ import annotations
from typing import List, Optional, Tuple

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
    category = Category(name=data.name)
    await category.insert()
    return category


async def get_category(category_id: str) -> Optional[Category]:
    return await Category.get(category_id)


async def update_category(category_id: str, data: CategoryUpdate) -> Optional[Category]:
    category = await Category.get(category_id)
    if not category:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    await category.save()
    return category


async def delete_category(category_id: str) -> bool:
    category = await Category.get(category_id)
    if not category:
        return False
    await category.delete()
    return True


async def list_products_by_category(categoryId: str) -> List[Product]:
    return (
        await Product.find(Product.categoryId == categoryId)
        .sort("CreatedAt")
        .to_list()
    )
