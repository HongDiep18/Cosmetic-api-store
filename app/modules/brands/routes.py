from fastapi import APIRouter, HTTPException, Query, status

from app.modules.brands.schemas import BrandCreate, BrandOut, BrandUpdate
from app.modules.brands.controller import (
    create_brand,
    delete_brand,
    get_brand,
    list_brands,
    update_brand,
)


router = APIRouter()


@router.post("/", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand_endpoint(data: BrandCreate):
    brand = await create_brand(data)
    return BrandOut.model_validate(brand, from_attributes=True)


@router.get("", response_model=list[BrandOut])
@router.get("/", response_model=list[BrandOut])
async def list_brands_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(200, ge=1, le=500),
):
    brands, _ = await list_brands(page=page, limit=limit)
    return [BrandOut.model_validate(b, from_attributes=True) for b in brands]


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand_endpoint(brand_id: str):
    brand = await get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return BrandOut.model_validate(brand, from_attributes=True)


@router.put("/{brand_id}", response_model=BrandOut)
async def update_brand_endpoint(brand_id: str, data: BrandUpdate):
    brand = await update_brand(brand_id, data)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return BrandOut.model_validate(brand, from_attributes=True)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand_endpoint(brand_id: str):
    ok = await delete_brand(brand_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return None


