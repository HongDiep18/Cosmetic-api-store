# -*- coding: utf-8 -*-
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
from beanie import PydanticObjectId
from fastapi.responses import JSONResponse

from app.core.deps import require_admin_account
from app.modules.products.model import Product
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate, PaginatedResponse, StockUpdateRequest
from app.modules.products.utils import save_upload_file
from app.modules.products.controller import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
    get_products_stats,
    get_product_detail,
)

router = APIRouter()


async def convert_product_to_out(product: Product) -> ProductOut:
    try:
        # Get raw document data to check for old field names
        from beanie import PydanticObjectId
        from app.modules.products.model import Product as ProductModel
        
        # Try to get raw document from MongoDB
        raw_doc = None
        try:
            # Access the internal document directly from collection
            if hasattr(product, 'id'):
                from app.db.init import db
                raw_doc = await db.products.find_one({'_id': product.id})
        except Exception as e:
            print(f"Could not get raw document: {e}")
        
        # Try to get product data - check both new and old field names
        product_name = None
        description = None
        price = None
        stock = None
        
        # First try new field names
        try:
            product_name = getattr(product, 'productName', None)
            description = getattr(product, 'description', None)
            price = getattr(product, 'price', None)
            stock = getattr(product, 'stock', None)
        except:
            pass
        
        # If not found, try old field names from raw document
        if not product_name and raw_doc:
            product_name = raw_doc.get('ProductName') or raw_doc.get('productName')
            description = raw_doc.get('Description') or raw_doc.get('description')
            price = raw_doc.get('Price') or raw_doc.get('price')
            stock = raw_doc.get('Stock') or raw_doc.get('stock')
        
        # If still not found, try getattr with old names
        if not product_name:
            product_name = getattr(product, 'ProductName', None)
            description = getattr(product, 'Description', None)
            price = getattr(product, 'Price', None)
            stock = getattr(product, 'Stock', None)
        
        # Build converted dict
        converted = {
            'productName': product_name or '',
            'description': description or '',
            'price': float(price) if price is not None else 0.0,
            'originalPrice': getattr(product, 'originalPrice', None) or getattr(product, 'OriginalPrice', None),
            'stock': int(stock) if stock is not None else 0,
            'status': getattr(product, 'status', None) or getattr(product, 'Status', 'available'),
            'image': getattr(product, 'image', None) or getattr(product, 'Image', None),
            'rating': getattr(product, 'rating', None) or getattr(product, 'Rating', 0.0),
            'reviewCount': getattr(product, 'reviewCount', None) or getattr(product, 'ReviewCount', 0),
            'isFeatured': getattr(product, 'isFeatured', None) or getattr(product, 'IsFeatured', False),
            'isNew': getattr(product, 'isNew', None) or getattr(product, 'IsNew', False),
            'createdAt': getattr(product, 'createdAt', None) or getattr(product, 'CreatedAt', None),
            'updatedAt': getattr(product, 'updatedAt', None) or getattr(product, 'UpdatedAt', None),
            '_id': str(product.id) if hasattr(product, 'id') else str(getattr(product, '_id', '')),
        }
        
        # Convert category - check both new and old format
        category = getattr(product, 'category', None)
        category_id = None
        category_name = None
        
        if category:
            # Already in new format
            if hasattr(category, 'categoryId') or (isinstance(category, dict) and 'categoryId' in category):
                converted['category'] = category
            else:
                # It's a CategoryEmbedded object, use as is
                converted['category'] = category
        else:
            # Try old format - first from raw document
            if raw_doc:
                category_id = raw_doc.get('CategoryID')
                category_name = raw_doc.get('CategoryName')
            
            # If not in raw doc, try getattr
            if not category_id:
                category_id = getattr(product, 'CategoryID', None)
                category_name = getattr(product, 'CategoryName', None)
            if category_id or category_name:
                from app.modules.products.model import CategoryEmbedded
                try:
                    converted['category'] = CategoryEmbedded(
                        categoryId=PydanticObjectId(category_id) if category_id else PydanticObjectId(),
                        name=category_name or ''
                    )
                except:
                    # If conversion fails, try to fetch from database
                    from app.modules.categories.model import Category
                    from bson import ObjectId
                    if category_id and ObjectId.is_valid(category_id):
                        cat = await Category.get(ObjectId(category_id))
                        if cat:
                            converted['category'] = CategoryEmbedded(
                                categoryId=cat.id,
                                name=cat.CategoryName
                            )
                        else:
                            converted['category'] = CategoryEmbedded(
                                categoryId=PydanticObjectId(),
                                name=category_name or ''
                            )
                    else:
                        converted['category'] = CategoryEmbedded(
                            categoryId=PydanticObjectId(),
                            name=category_name or ''
                        )
            else:
                # No category found, create empty one
                from app.modules.products.model import CategoryEmbedded
                converted['category'] = CategoryEmbedded(
                    categoryId=PydanticObjectId(),
                    name=''
                )
        
        # Convert brand - check both new and old format
        brand = getattr(product, 'brand', None)
        brand_id = None
        brand_name = None
        
        if brand:
            converted['brand'] = brand
        else:
            # Try old format - first from raw document
            if raw_doc:
                brand_id = raw_doc.get('BrandID')
                brand_name = raw_doc.get('BrandName') or raw_doc.get('Brand')
            
            # If not in raw doc, try getattr
            if not brand_id:
                brand_id = getattr(product, 'BrandID', None)
                brand_name = getattr(product, 'BrandName', None) or getattr(product, 'Brand', None)
            if brand_id or brand_name:
                from app.modules.products.model import BrandEmbedded
                try:
                    converted['brand'] = BrandEmbedded(
                        brandId=PydanticObjectId(brand_id) if brand_id else PydanticObjectId(),
                        name=brand_name or ''
                    )
                except:
                    # If conversion fails, try to fetch from database
                    from app.modules.brands.model import Brand
                    from bson import ObjectId
                    if brand_id and ObjectId.is_valid(brand_id):
                        br = await Brand.get(ObjectId(brand_id))
                        if br:
                            converted['brand'] = BrandEmbedded(
                                brandId=br.id,
                                name=br.BrandName
                            )
                        else:
                            converted['brand'] = None
                    else:
                        converted['brand'] = None
            else:
                converted['brand'] = None
        
        return ProductOut.model_validate(converted, from_attributes=True)
    except Exception as e:
        print(f"Error converting product {getattr(product, 'id', 'unknown')}: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/stats")
async def get_products_stats_endpoint():
    return await get_products_stats()


@router.get("/test")
async def test_products_endpoint():
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
)
@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product_endpoint(data: ProductCreate):
    try:
        product = await create_product(data)
        return await convert_product_to_out(product)
    except Exception as e:
        print(f"Error creating product: {str(e)}")
        import traceback
        traceback.print_exc()
        if "validation" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse)
@router.get("/", response_model=PaginatedResponse)
async def list_products_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str | None = None,
    categoryId: str | None = None,
    brandId: str | None = None,
    includeDiscontinued: bool = Query(False),
):
    try:
        products, total = await list_products(
            page=page, limit=limit, name=name, categoryId=categoryId, brandId=brandId, includeDiscontinued=includeDiscontinued
        )
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        product_out_list = []
        for p in products:
            try:
                product_out_list.append(await convert_product_to_out(p))
            except Exception as e:
                print(f"Skipping product due to conversion error: {e}")
                continue
        
        return PaginatedResponse(
            data=product_out_list,
            total=total,
            page=page,
            limit=limit,
            totalPages=total_pages,
        )
    except Exception as e:
        print(f"Error in list_products_endpoint: {e}")
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
    return await convert_product_to_out(product)


@router.patch(
    "/{product_id}",
    response_model=ProductOut,
)
async def update_product_endpoint(product_id: str, data: ProductUpdate):
    product = await update_product(product_id, data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return await convert_product_to_out(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
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
    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400, content={"error": "File uploaded is not an image"}
        )

    MAX_SIZE = 5 * 1024 * 1024
    content = await file.read()
    await file.seek(0)

    if len(content) > MAX_SIZE:
        return JSONResponse(
            status_code=400,
            content={"error": "File size too large. Maximum size is 5MB"},
        )

    try:
        base_url = "http://localhost:8000"
        if request:
            base_url = str(request.base_url).rstrip("/")
        
        file_url = await save_upload_file(file, base_url)
        return {"url": file_url}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error uploading file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred while uploading the file: {str(e)}"},
        )


@router.get("/{product_id}/detail")
async def get_product_detail_endpoint(product_id: str):
    product_detail = await get_product_detail(product_id)
    if not product_detail:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_detail


@router.put("/{product_id}/stock")
async def update_stock(product_id: str, data: StockUpdateRequest):
    product = await Product.get(PydanticObjectId(product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.stock = data.quantity
    await product.save()

    return {"message": "Cập nhật tồn kho thành công"}
