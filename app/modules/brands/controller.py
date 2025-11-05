from __future__ import annotations
from typing import List, Tuple, Optional

from app.modules.brands.model import Brand
from app.modules.brands.schemas import BrandCreate, BrandUpdate


async def list_brands(page: int = 1, limit: int = 200) -> Tuple[List[Brand], int]:
    page = max(page, 1)
    limit = max(limit, 1)
    query = Brand.find_all()
    total = await query.count()
    items = await query.sort("CreatedAt").skip((page - 1) * limit).limit(limit).to_list()
    return items, total


async def create_brand(data: BrandCreate) -> Brand:
    brand = Brand(**data.model_dump())
    await brand.insert()
    return brand


async def get_brand(brand_id: str) -> Optional[Brand]:
    return await Brand.get(brand_id)


async def update_brand(brand_id: str, data: BrandUpdate) -> Optional[Brand]:
    brand = await Brand.get(brand_id)
    if not brand:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    await brand.save()
    return brand


async def delete_brand(brand_id: str) -> bool:
    brand = await Brand.get(brand_id)
    if not brand:
        return False
    await brand.delete()
    return True


