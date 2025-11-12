from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import re

from app.modules.brands.model import Brand
from app.modules.brands.schemas import BrandCreate, BrandUpdate
from app.modules.products.model import Product


_SLUGIFY_PATTERN = re.compile(r"[^a-z0-9]+")


def _normalize_name(value: str) -> str:
    return " ".join(value.split()).strip()


def _slugify(value: str) -> str:
    normalized = _normalize_name(value).lower()
    slug = _SLUGIFY_PATTERN.sub("-", normalized).strip("-")
    return slug or "brand"


async def _collect_brands_from_products() -> List[Dict[str, object]]:
    """Thu thập danh sách thương hiệu duy nhất từ collection products."""

    collection = Product.get_motor_collection()
    cursor = collection.find(
        {
            "Brand": {
                "$exists": True,
                "$ne": None,
                "$ne": "",
            }
        },
        {
            "Brand": 1,
            "CreatedAt": 1,
            "UpdatedAt": 1,
        },
    )

    brands: Dict[str, Dict[str, object]] = {}

    async for doc in cursor:
        name = doc.get("Brand")
        if not isinstance(name, str):
            continue
        name = _normalize_name(name)
        if not name:
            continue

        key = name.lower()
        created_at = doc.get("CreatedAt")
        updated_at = doc.get("UpdatedAt")

        entry = brands.get(key)
        if entry is None:
            brands[key] = {
                "BrandName": name,
                "CreatedAt": created_at,
                "UpdatedAt": updated_at,
            }
            continue

        if created_at:
            existing_created = entry.get("CreatedAt")
            if existing_created is None or created_at < existing_created:
                entry["CreatedAt"] = created_at

        if updated_at:
            existing_updated = entry.get("UpdatedAt")
            if existing_updated is None or updated_at > existing_updated:
                entry["UpdatedAt"] = updated_at

    results: List[Dict[str, object]] = []
    for entry in brands.values():
        name = entry["BrandName"]
        created_at = entry.get("CreatedAt") or datetime.utcnow()
        updated_at = entry.get("UpdatedAt") or created_at
        results.append(
            {
                "id": _slugify(name),
                "BrandName": name,
                "CreatedAt": created_at,
                "UpdatedAt": updated_at,
            }
        )

    results.sort(key=lambda item: str(item["BrandName"]).lower())
    return results


async def list_brands(page: int = 1, limit: int = 200) -> Tuple[List[dict], int]:
    page = max(page, 1)
    limit = max(limit, 1)
    derived_brands = await _collect_brands_from_products()
    if derived_brands:
        total = len(derived_brands)
        start = (page - 1) * limit
        end = start + limit
        items = derived_brands[start:end]
        return items, total

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


