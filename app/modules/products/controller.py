from __future__ import annotations
from typing import List, Optional, Tuple

from beanie.operators import RegEx

from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductUpdate


def _build_filters(name: Optional[str], categoryId: Optional[str]):
    filters = []
    if name:
        filters.append(Product.ProductName.match(RegEx(name, options="i")))
    if categoryId:
        filters.append(Product.CategoryID == categoryId)
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
        await query.sort("-CreatedAt").skip((page - 1) * limit).limit(limit).to_list()
    )
    return items, total


async def create_product(data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    await product.insert()
    return product


async def get_product(product_id: str) -> Optional[Product]:
    # Tìm theo ProductID (trường nghiệp vụ) thay vì _id ObjectId
    return await Product.find_one(Product.ProductID == product_id)


async def update_product(product_id: str, data: ProductUpdate) -> Optional[Product]:
    product = await Product.find_one(Product.ProductID == product_id)
    if not product:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    await product.save()
    return product


async def delete_product(product_id: str) -> bool:
    product = await Product.find_one(Product.ProductID == product_id)
    if not product:
        return False
    await product.delete()
    return True

#get số lượng sản phẩm sắp hết (Stock <= 5)
async def get_low_stock_products_count(threshold: int = 5) -> int:
    """
    Trả về số lượng sản phẩm có stock <= threshold.
    """
    low_stock_count = await Product.find_many(Product.Stock <= threshold).count()
    return low_stock_count


async def get_products_stats() -> dict:
    # Đọc tất cả sản phẩm và tính toán an toàn ở Python (chịu dữ liệu Price/Stock dạng chuỗi)
    items = await Product.find_all().to_list()

    def to_number(value) -> float:
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = value.replace(',', '').strip()
                return float(cleaned)
        except Exception:
            return 0.0
        return 0.0

    total = len(items)
    out_of_stock = 0
    low_stock = 0
    available = 0
    total_value = 0.0

    for p in items:
        stock = to_number(getattr(p, "Stock", 0))
        price = to_number(getattr(p, "Price", 0))
        total_value += price * stock
        if stock <= 0:
            out_of_stock += 1
        elif stock <= 10:
            low_stock += 1
        else:
            available += 1

    return {
        "total": total,
        "available": available,
        "lowStock": low_stock,
        "outOfStock": out_of_stock,
        "totalValue": total_value,
    }
