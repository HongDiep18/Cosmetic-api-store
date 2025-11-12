from __future__ import annotations
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import re

from bson import ObjectId

from app.modules.categories.model import Category
from app.modules.products.model import Product
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate


_SLUGIFY_PATTERN = re.compile(r"[^a-z0-9]+")


def _normalize_name(value: str) -> str:
    return " ".join(value.split()).strip()


def _sanitize_id(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="ignore")
    value = str(value).strip()
    if value.lower() in {"", "null", "undefined"}:
        return None
    return value


def _slugify(value: str) -> str:
    normalized = _normalize_name(value).lower()
    slug = _SLUGIFY_PATTERN.sub("-", normalized).strip("-")
    return slug or "category"


async def _collect_categories_from_products() -> List[Dict[str, object]]:
    """Thu thập danh mục duy nhất từ collection products."""

    collection = Product.get_motor_collection()
    cursor = collection.find(
        {
            "CategoryName": {
                "$exists": True,
                "$ne": None,
                "$ne": "",
            }
        },
        {
            "CategoryName": 1,
            "CategoryID": 1,
            "CreatedAt": 1,
            "UpdatedAt": 1,
        },
    )

    categories: Dict[str, Dict[str, object]] = {}

    async for doc in cursor:
        name = doc.get("CategoryName")
        if not isinstance(name, str):
            continue
        name = _normalize_name(name)
        if not name:
            continue

        key = name.lower()
        candidate_id = _sanitize_id(doc.get("CategoryID"))
        created_at = doc.get("CreatedAt")
        updated_at = doc.get("UpdatedAt")

        entry = categories.get(key)
        if entry is None:
            categories[key] = {
                "CategoryName": name,
                "CategoryID": candidate_id,
                "CreatedAt": created_at,
                "UpdatedAt": updated_at,
            }
            continue

        if not entry.get("CategoryID") and candidate_id:
            entry["CategoryID"] = candidate_id

        if created_at:
            existing_created = entry.get("CreatedAt")
            if existing_created is None or created_at < existing_created:
                entry["CreatedAt"] = created_at

        if updated_at:
            existing_updated = entry.get("UpdatedAt")
            if existing_updated is None or updated_at > existing_updated:
                entry["UpdatedAt"] = updated_at

    results: List[Dict[str, object]] = []
    for entry in categories.values():
        name = entry["CategoryName"]
        category_id = entry.get("CategoryID") or _slugify(str(name))
        created_at = entry.get("CreatedAt") or datetime.utcnow()
        updated_at = entry.get("UpdatedAt") or created_at
        results.append(
            {
                "CategoryID": str(category_id),
                "CategoryName": name,
                "Description": None,
                "CreatedAt": created_at,
                "UpdatedAt": updated_at,
            }
        )

    results.sort(key=lambda item: str(item["CategoryName"]).lower())
    return results


async def list_categories(page: int = 1, limit: int = 50) -> Tuple[List[dict], int]:
    page = max(page, 1)
    limit = max(limit, 1)
    derived_categories = await _collect_categories_from_products()
    if derived_categories:
        total = len(derived_categories)
        start = (page - 1) * limit
        end = start + limit
        items = derived_categories[start:end]
        return items, total

    # Fallback: sử dụng collection categories nếu không có dữ liệu phù hợp trong products
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
    return (
        await Product.find_many(Product.CategoryID == categoryId)
        .sort("CreatedAt")
        .to_list()
    )
