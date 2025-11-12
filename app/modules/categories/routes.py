from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime

from app.core.deps import require_admin_account
from app.modules.categories.constants import CATEGORY_NOT_FOUND
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    CategoryListItem,
)
from app.modules.categories.controller import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    list_products_by_category,
    update_category,
)
from app.modules.products.schemas import ProductOut
from bson import ObjectId


router = APIRouter()


@router.post(
    "/",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    # # dependencies=[Depends(require_admin_account)],
)
async def create_category_endpoint(data: CategoryCreate):
    category = await create_category(data)
    return CategoryOut.model_validate(category, from_attributes=True)


@router.get("", response_model=list[CategoryListItem])  # Không có trailing slash
@router.get("/", response_model=list[CategoryListItem])  # Có trailing slash
async def list_categories_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    categories, _ = await list_categories(page=page, limit=limit)
    normalized: list[CategoryListItem] = []

    for item in categories:
        if isinstance(item, dict):
            normalized.append(CategoryListItem(**item))
        else:
            created_at = getattr(item, "CreatedAt", None) or datetime.utcnow()
            updated_at = getattr(item, "UpdatedAt", None) or created_at
            normalized.append(
                CategoryListItem(
                    CategoryID=str(getattr(item, "id", getattr(item, "_id", ""))),
                    CategoryName=getattr(item, "CategoryName", ""),
                    Description=getattr(item, "Description", None),
                    CreatedAt=created_at,
                    UpdatedAt=updated_at,
                )
            )

    return normalized


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category_endpoint(category_id: str):
    category = await get_category(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CATEGORY_NOT_FOUND
        )
    return CategoryOut.model_validate(category, from_attributes=True)


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_category_endpoint(category_id: str, data: CategoryUpdate):
    category = await update_category(category_id, data)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CATEGORY_NOT_FOUND
        )
    return CategoryOut.model_validate(category, from_attributes=True)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    # dependencies=[Depends(require_admin_account)],
)
async def delete_category_endpoint(category_id: str):
    ok = await delete_category(category_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CATEGORY_NOT_FOUND
        )
    return None


@router.get("/{categoryId}/products", response_model=list[ProductOut])
async def list_products_by_category_endpoint(categoryId: str):
    products = await list_products_by_category(categoryId)
    return [ProductOut.model_validate(p, from_attributes=True) for p in products]
