from __future__ import annotations
from typing import List, Optional, Tuple

from beanie.operators import RegEx

from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductUpdate


def _build_filters(name: Optional[str], categoryId: Optional[str]):
    filters = []
    if name:
        filters.append(Product.name.match(RegEx(name, options="i")))
    if categoryId:
        filters.append(Product.categoryId == categoryId)
    return filters


async def list_products(
    page: int = 1,
    limit: int = 10,
    name: Optional[str] = None,
    categoryId: Optional[str] = None,
) -> Tuple[List[Product], int]:
    page = max(page, 1)
    limit = max(limit, 1)

    filters = _build_filters(name, categoryId)
    query = Product.find_many(*filters) if filters else Product.find_all()

    total = await query.count()
    items = (
        await query.sort("-createdAt").skip((page - 1) * limit).limit(limit).to_list()
    )
    return items, total


async def create_product(data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    await product.insert()
    return product


async def get_product(product_id: str) -> Optional[Product]:
    return await Product.get(product_id)


async def update_product(product_id: str, data: ProductUpdate) -> Optional[Product]:
    product = await Product.get(product_id)
    if not product:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    await product.save()
    return product


async def delete_product(product_id: str) -> bool:
    product = await Product.get(product_id)
    if not product:
        return False
    await product.delete()
    return True
