from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_admin_account
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate
from app.modules.products.controller import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)

router = APIRouter()


@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_account)],
)
async def create_product_endpoint(data: ProductCreate):
    product = await create_product(data)
    return ProductOut.model_validate(product, from_attributes=True)


@router.get("/", response_model=list[ProductOut])
async def list_products_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str | None = None,
    categoryId: str | None = None,
):
    products, _ = await list_products(
        page=page, limit=limit, name=name, categoryId=categoryId
    )
    return [ProductOut.model_validate(p, from_attributes=True) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product_endpoint(product_id: str):
    product = await get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductOut.model_validate(product, from_attributes=True)


@router.patch(
    "/{product_id}",
    response_model=ProductOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_product_endpoint(product_id: str, data: ProductUpdate):
    product = await update_product(product_id, data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return ProductOut.model_validate(product, from_attributes=True)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_account)],
)
async def delete_product_endpoint(product_id: str):
    ok = await delete_product(product_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return None
