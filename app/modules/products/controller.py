# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional, Tuple
from beanie.operators import RegEx
from bson import ObjectId
from beanie import PydanticObjectId

from app.modules.products.model import Product, CategoryEmbedded, BrandEmbedded
from app.modules.products.schemas import ProductCreate, ProductUpdate
from app.modules.categories.model import Category
from app.modules.brands.model import Brand


def _build_filters(
    name: Optional[str], 
    categoryId: Optional[str],
    brandId: Optional[str] = None,
    includeDiscontinued: bool = False
):
    filters = []
    if name:
        filters.append(Product.productName.match(RegEx(name, options="i")))
    if categoryId:
        filters.append(Product.category.categoryId == PydanticObjectId(categoryId))
    if brandId:
        filters.append(Product.brand.brandId == PydanticObjectId(brandId))
    if not includeDiscontinued:
        filters.append(Product.status != "Discontinued")
    return filters


async def list_products(
    page: int = 1,
    limit: int = 10,
    name: Optional[str] = None,
    categoryId: Optional[str] = None,
    brandId: Optional[str] = None,
    includeDiscontinued: bool = False,
) -> Tuple[List[Product], int]:
    page = max(page, 1)
    limit = max(limit, 1)

    filters = _build_filters(name, categoryId, brandId, includeDiscontinued)
    query = Product.find_many(*filters) if filters else Product.find_all()

    total = await query.count()
    items = (
        await query.sort("-createdAt").skip((page - 1) * limit).limit(limit).to_list()
    )
    return items, total


async def create_product(data: ProductCreate) -> Product:
    try:
        product_data = data.model_dump()
        
        # Fetch category from database to get name
        category_embedded = None
        if "category" in product_data and product_data["category"]:
            category_info = product_data["category"]
            category_id = category_info.get("categoryId")
            if category_id:
                category = await Category.get(ObjectId(category_id))
                if not category:
                    raise ValueError(f"Category with ID {category_id} not found")
                category_embedded = CategoryEmbedded(
                    categoryId=category.id,
                    name=category.CategoryName
                )
            else:
                raise ValueError("Category ID is required")
        else:
            raise ValueError("Category is required")
        
        # Fetch brand from database to get name
        brand_embedded = None
        if "brand" in product_data and product_data["brand"]:
            brand_info = product_data["brand"]
            brand_id = brand_info.get("brandId")
            if brand_id:
                brand = await Brand.get(ObjectId(brand_id))
                if brand:
                    brand_embedded = BrandEmbedded(
                        brandId=brand.id,
                        name=brand.BrandName
                    )
        
        # Create product with embedded data
        product = Product(
            productName=product_data.get("productName", ""),
            description=product_data.get("description", ""),
            price=product_data.get("price", 0),
            originalPrice=product_data.get("originalPrice"),
            stock=product_data.get("stock", 0),
            status=product_data.get("status", "available"),
            image=product_data.get("image"),
            rating=product_data.get("rating", 0.0),
            reviewCount=product_data.get("reviewCount", 0),
            isFeatured=product_data.get("isFeatured", False),
            isNew=product_data.get("isNew", False),
            category=category_embedded,
            brand=brand_embedded
        )
        await product.insert()
        return product
    except Exception as e:
        print(f"Error in create_product: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def get_product(product_id: str) -> Optional[Product]:
    try:
        if ObjectId.is_valid(product_id):
            product = await Product.get(ObjectId(product_id))
            return product
    except Exception:
        pass
    return None


async def update_product(product_id: str, data: ProductUpdate) -> Optional[Product]:
    try:
        if ObjectId.is_valid(product_id):
            product = await Product.get(ObjectId(product_id))
            if product:
                update_data = data.model_dump(exclude_unset=True)
                
                # Handle category update - fetch from database
                if "category" in update_data and update_data["category"]:
                    category_info = update_data["category"]
                    category_id = category_info.get("categoryId")
                    if category_id:
                        category = await Category.get(ObjectId(category_id))
                        if not category:
                            raise ValueError(f"Category with ID {category_id} not found")
                        product.category = CategoryEmbedded(
                            categoryId=category.id,
                            name=category.CategoryName
                        )
                    update_data.pop("category")
                
                # Handle brand update - fetch from database
                if "brand" in update_data and update_data["brand"]:
                    brand_info = update_data["brand"]
                    brand_id = brand_info.get("brandId")
                    if brand_id:
                        brand = await Brand.get(ObjectId(brand_id))
                        if brand:
                            product.brand = BrandEmbedded(
                                brandId=brand.id,
                                name=brand.BrandName
                            )
                        else:
                            product.brand = None
                    else:
                        product.brand = None
                    update_data.pop("brand")
                
                # Update other fields
                for key, value in update_data.items():
                    setattr(product, key, value)
                await product.save()
                return product
    except Exception as e:
        print(f"Error updating product: {e}")
        import traceback
        traceback.print_exc()
    return None


async def delete_product(product_id: str) -> bool:
    try:
        if ObjectId.is_valid(product_id):
            product = await Product.get(ObjectId(product_id))
            if product:
                await product.delete()
                return True
    except Exception:
        pass
    return False


async def get_low_stock_products_count(threshold: int = 5) -> int:
    low_stock_count = await Product.find_many(Product.stock <= threshold).count()
    return low_stock_count


async def get_products_stats() -> dict:
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
        stock = to_number(getattr(p, "stock", 0))
        price = to_number(getattr(p, "price", 0))
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


async def get_product_detail(product_id: str) -> Optional[dict]:
    product = None
    if ObjectId.is_valid(product_id):
        product = await Product.get(ObjectId(product_id))

    if not product:
        return None

    category = getattr(product, "category", None)
    brand = getattr(product, "brand", None)
    
    return {
        "productName": getattr(product, "productName", None),
        "brand": brand.name if brand else None,
        "price": getattr(product, "price", None),
        "image": getattr(product, "image", None),
        "categoryName": category.name if category else None,
        "rating": getattr(product, "rating", None),
        "reviewCount": getattr(product, "reviewCount", None),
        "isNew": getattr(product, "isNew", None),
        "isFeatured": getattr(product, "isFeatured", None),
    }
