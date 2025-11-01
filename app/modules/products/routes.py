from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
    UploadFile,
    File,
)
from fastapi.responses import JSONResponse
from fastapi import Response
from fastapi.staticfiles import StaticFiles

from app.core.deps import require_admin_account
from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate
from app.modules.products.utils import save_upload_file
from app.modules.products.controller import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
    get_products_stats,
)

router = APIRouter()


@router.get("/stats")
async def get_products_stats_endpoint():
    return await get_products_stats()


@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    # # dependencies=[Depends(require_admin_account)],
)
async def create_product_endpoint(data: ProductCreate):
    product = await create_product(data)
    return ProductOut.model_validate(product, from_attributes=True)


@router.get("/", response_model=list[ProductOut])
async def list_products_endpoint(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str | None = None,
    categoryId: str | None = None,
):
    products, total = await list_products(
        page=page, limit=limit, name=name, categoryId=categoryId
    )
    response.headers["X-Total-Count"] = str(total)
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
    # dependencies=[Depends(require_admin_account)],
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
    # dependencies=[Depends(require_admin_account)],
)
async def delete_product_endpoint(product_id: str):
    ok = await delete_product(product_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return None


# @router.post("/upload/", # dependencies=[Depends(require_admin_account)])
# async def upload_image(
#     file: UploadFile = File(...),
#     request: Request = Depends(),
# ):
#     if not file.content_type or not file.content_type.startswith("image/"):
#         return JSONResponse(
#             status_code=400, content={"error": "File uploaded is not an image"}
#         )

#     # Check file size (max 5MB)
#     MAX_SIZE = 5 * 1024 * 1024  # 5MB
#     content = await file.read()
#     await file.seek(0)  # Reset file pointer

#     if len(content) > MAX_SIZE:
#         return JSONResponse(
#             status_code=400,
#             content={"error": "File size too large. Maximum size is 5MB"},
#         )

#     try:
#         # Get base URL from request
#         base_url = str(request.base_url).rstrip("/")
#         file_url = await save_upload_file(file, base_url)
#         return {"url": file_url}
#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={"error": f"An error occurred while uploading the file: {str(e)}"},
#         )


# # Get số lượng sản phẩm sắp hết (Stock <= 5)
# @router.get("/low-stock/count")
# async def low_stock_count_endpoint():
#     count = await get_low_stock_products_count()
#     return {"low_stock_count": count}


@router.get("/stats")
async def get_products_stats_endpoint():
    return await get_products_stats()
