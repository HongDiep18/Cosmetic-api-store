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
from fastapi.staticfiles import StaticFiles

from app.core.deps import require_admin_account
from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate, PaginatedResponse
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


def convert_product_to_out(product: Product) -> ProductOut:
    """Chuyển đổi Product document thành ProductOut schema"""
    try:
        # Sử dụng model_dump() của Beanie Document
        if hasattr(product, 'model_dump'):
            product_dict = product.model_dump()
        else:
            # Fallback: convert từ dict
            product_dict = dict(product)
        
        # Đảm bảo ProductID tồn tại (từ id của Beanie Document)
        if not product_dict.get("ProductID"):
            if hasattr(product, 'id') and product.id:
                product_dict["ProductID"] = str(product.id)
            elif hasattr(product, '_id') and product._id:
                product_dict["ProductID"] = str(product._id)
        
        # Xử lý các field có thể là None hoặc ObjectId
        if 'CategoryID' in product_dict and isinstance(product_dict['CategoryID'], dict):
            # Nếu CategoryID là dict (ObjectId serialized)
            if '$oid' in product_dict['CategoryID']:
                product_dict['CategoryID'] = product_dict['CategoryID']['$oid']
        
        return ProductOut(**product_dict)
    except Exception as e:
        print(f"❌ Error converting product {getattr(product, 'id', 'unknown')}: {e}")
        raise


@router.get("/stats")
async def get_products_stats_endpoint():
    return await get_products_stats()


@router.get("/test")
async def test_products_endpoint():
    """Test endpoint để kiểm tra products router hoạt động"""
    try:
        count = await Product.find_all().count()
        return {
            "status": "ok",
            "message": "Products router is working",
            "total_products_in_db": count,
            "router_path": "/api/products"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    # # dependencies=[Depends(require_admin_account)],
)
@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    # # dependencies=[Depends(require_admin_account)],
)
async def create_product_endpoint(data: ProductCreate):
    print(f"📦 Creating product with data: {data.model_dump()}")
    print(f"📦 Product Image: {data.Image}")
    product = await create_product(data)
    print(f"✅ Product created: {product.ProductID}, Image: {product.Image}")
    return convert_product_to_out(product)


@router.get("", response_model=PaginatedResponse)  # Không có trailing slash
@router.get("/", response_model=PaginatedResponse)  # Có trailing slash
async def list_products_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str | None = None,
    categoryId: str | None = None,
    includeDiscontinued: bool = Query(False, description="Bao gồm sản phẩm đã vô hiệu hóa (dành cho admin)"),
):
    try:
        products, total = await list_products(
            page=page, limit=limit, name=name, categoryId=categoryId, includeDiscontinued=includeDiscontinued
        )
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        # Convert products với error handling
        product_out_list = []
        for p in products:
            try:
                product_out_list.append(convert_product_to_out(p))
            except Exception as e:
                print(f"⚠️ Skipping product due to conversion error: {e}")
                continue
        
        return PaginatedResponse(
            data=product_out_list,
            total=total,
            page=page,
            limit=limit,
            totalPages=total_pages,
        )
    except Exception as e:
        print(f"❌ Error in list_products_endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching products: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product_endpoint(product_id: str):
    product = await get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return convert_product_to_out(product)


@router.patch(
    "/{product_id}",
    response_model=ProductOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_product_endpoint(product_id: str, data: ProductUpdate):
    print(f"📦 Updating product {product_id} with data: {data.model_dump(exclude_unset=True)}")
    print(f"📦 Product Image: {data.Image}")
    product = await update_product(product_id, data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    print(f"✅ Product updated: {product.ProductID}, Image: {product.Image}")
    return convert_product_to_out(product)


@router.patch(
    "/{product_id}/stock",
    response_model=ProductOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_product_stock(product_id: str, payload: dict):
    """
    Cập nhật tồn kho (stock) cho 1 sản phẩm.
    Dùng khi admin muốn trừ/thêm stock thủ công.
    """
    stock_value = payload.get("stock")
    if stock_value is None:
        raise HTTPException(status_code=400, detail="stock is required")

    # Lấy sản phẩm
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Cập nhật tồn kho
    try:
        change_value = payload.get("change")  # ví dụ: -2 hoặc +5
        if change_value is not None:
            product.Stock += change_value
        else:
            product.Stock = stock_value
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stock: {str(e)}")

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


@router.post("/upload/")
async def upload_image(
    file: UploadFile = File(...),
    request: Request = None,
):
    """Upload image file and return the URL"""
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400, content={"error": "File uploaded is not an image"}
        )

    # Check file size (max 5MB)
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    await file.seek(0)  # Reset file pointer

    if len(content) > MAX_SIZE:
        return JSONResponse(
            status_code=400,
            content={"error": "File size too large. Maximum size is 5MB"},
        )

    try:
        # Get base URL from request
        base_url = "http://localhost:8000"
        if request:
            base_url = str(request.base_url).rstrip("/")
        
        print(f"📤 Uploading file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Save file and get URL
        file_url = await save_upload_file(file, base_url)
        
        # Log để debug
        print(f"✅ Image uploaded successfully: {file_url}")
        
        return {"url": file_url}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error uploading file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred while uploading the file: {str(e)}"},
        )


# # Get số lượng sản phẩm sắp hết (Stock <= 5)
# @router.get("/low-stock/count")
# async def low_stock_count_endpoint():
#     count = await get_low_stock_products_count()
#     return {"low_stock_count": count}



# lấy chi tiết sản phẩm cho trang chi tiết sản phẩm
@router.get("/{product_id}/detail")
async def get_product_detail_endpoint(product_id: str):
    """
    Trả về chi tiết sản phẩm chỉ gồm các trường cơ bản:
    ProductName, Brand, Price, Image, CategoryName, Rating, ReviewCount, IsNew, IsFeatured
    """
    from app.modules.products.controller import get_product_detail

    product_detail = await get_product_detail(product_id)
    if not product_detail:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_detail
