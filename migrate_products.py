"""
Script Migration: Gộp products, categories, brands thành 1 collection products với embedded structure
Chạy script này CHỈ MỘT LẦN để di chuyển dữ liệu từ cấu trúc cũ sang cấu trúc mới.

Cấu trúc cũ:
- products: ProductName, Description, Price, Stock, CategoryID, BrandID, Brand, CategoryName, ...
- categories: _id, CategoryName, Description, ...
- brands: _id, BrandName, ...

Cấu trúc mới:
- products: productName, description, price, stock, category: {categoryId, name}, brand: {brandId, name}, ...

Usage:
    python migrate_products.py
"""

# python E:/Subject/No_SQL/Web_NoSQL/react-cosmetic-api/migrate_products.py
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.core.config import settings


def get_mongodb_uri() -> str:
    """
    Lấy MongoDB URI, ưu tiên:
    1. Environment variable MONGODB_URI
    2. Localhost với port phổ biến (27018, 27017) nếu không có env
    3. Settings mặc định (Docker)
    """
    # Kiểm tra env variable trước
    env_uri = os.getenv("MONGODB_URI")
    if env_uri:
        print("📌 Sử dụng MONGODB_URI từ environment variable")
        return env_uri

    # Nếu không có env, thử localhost (cho máy local)
    default_uri = settings.MONGODB_URI

    # Nếu URI chứa "mongodb:" (Docker hostname), thử localhost với các port phổ biến
    if "mongodb://mongodb:" in default_uri or "mongodb://mongodb/" in default_uri:
        # Lấy database name từ URI
        db_name = (
            default_uri.split("/")[-1] if "/" in default_uri else settings.MONGODB_DB
        )

        # Thử port 27018 trước (thường dùng trong Docker với port mapping)
        local_uri_27018 = f"mongodb://localhost:27018/{db_name}"
        print("⚠️  Phát hiện Docker hostname 'mongodb'")
        print("   Thử kết nối với localhost:27018 (port mapping phổ biến trong Docker)")
        return local_uri_27018

    return default_uri


# Flag để đảm bảo chỉ chạy một lần
MIGRATION_FLAG_COLLECTION = "migration_flags"
MIGRATION_FLAG_NAME = "products_embedded_migration_v1"


async def check_migration_done(db) -> bool:
    """Kiểm tra xem migration đã chạy chưa"""
    flag_collection = db[MIGRATION_FLAG_COLLECTION]
    flag = await flag_collection.find_one({"name": MIGRATION_FLAG_NAME})
    return flag is not None


async def mark_migration_done(db):
    """Đánh dấu migration đã hoàn thành"""
    flag_collection = db[MIGRATION_FLAG_COLLECTION]
    await flag_collection.insert_one(
        {
            "name": MIGRATION_FLAG_NAME,
            "completed_at": datetime.utcnow(),
            "description": "Gộp products, categories, brands thành 1 collection products với embedded structure",
        }
    )


async def migrate_products(db):
    """
    Gộp products, categories, brands thành collection products với embedded structure
    """
    print("🔄 Đang migrate products với embedded categories và brands...")

    products_collection = db["products"]
    categories_collection = db["categories"]
    brands_collection = db["brands"]

    # Lấy tất cả categories và brands để tạo mapping
    categories = await categories_collection.find({}).to_list(length=None)
    brands = await brands_collection.find({}).to_list(length=None)

    # Tạo mapping CategoryID -> CategoryName (hỗ trợ cả ObjectId và string)
    category_map: Dict[str, Dict[str, Any]] = {}
    for cat in categories:
        cat_id_obj = cat.get("_id")
        if cat_id_obj:
            # Lưu cả ObjectId và string để tìm kiếm dễ dàng
            cat_id_str = str(cat_id_obj)
            cat_name = cat.get("CategoryName", "") or cat.get("categoryName", "")
            category_map[cat_id_str] = {
                "categoryId": cat_id_obj,  # Giữ ObjectId
                "name": cat_name
            }
            # Nếu có ObjectId, cũng lưu dạng string để tìm
            if isinstance(cat_id_obj, ObjectId):
                category_map[str(cat_id_obj)] = {
                    "categoryId": cat_id_obj,
                    "name": cat_name
                }

    # Tạo mapping BrandID -> BrandName (hỗ trợ cả ObjectId và string)
    brand_map: Dict[str, Dict[str, Any]] = {}
    for brand in brands:
        brand_id_obj = brand.get("_id")
        if brand_id_obj:
            brand_id_str = str(brand_id_obj)
            brand_name = brand.get("BrandName", "") or brand.get("brandName", "")
            brand_map[brand_id_str] = {
                "brandId": brand_id_obj,  # Giữ ObjectId
                "name": brand_name
            }
            # Nếu có ObjectId, cũng lưu dạng string để tìm
            if isinstance(brand_id_obj, ObjectId):
                brand_map[str(brand_id_obj)] = {
                    "brandId": brand_id_obj,
                    "name": brand_name
                }

    print(f"   📊 Tìm thấy: {len(categories)} categories, {len(brands)} brands")

    # Lấy tất cả products
    products = await products_collection.find({}).to_list(length=None)
    print(f"   📊 Tìm thấy {len(products)} products cần migrate")

    migrated_count = 0
    skipped_count = 0
    updated_count = 0

    for product in products:
        try:
            product_id = product.get("_id")
            if not product_id:
                skipped_count += 1
                continue

            # Kiểm tra xem product đã có cấu trúc mới chưa
            has_new_structure = (
                "category" in product and isinstance(product.get("category"), dict) and "categoryId" in product.get("category", {})
            )

            if has_new_structure:
                # Product đã có cấu trúc mới, bỏ qua
                updated_count += 1
                continue

            # Lấy dữ liệu từ product cũ
            product_name = product.get("ProductName") or product.get("productName", "")
            description = product.get("Description") or product.get("description", "")
            price = product.get("Price") or product.get("price", 0)
            original_price = product.get("OriginalPrice") or product.get("originalPrice")
            stock = product.get("Stock") or product.get("stock", 0)
            status = product.get("Status") or product.get("status", "available")
            image = product.get("Image") or product.get("image")
            rating = product.get("Rating") or product.get("rating", 0.0)
            review_count = product.get("ReviewCount") or product.get("reviewCount", 0)
            is_featured = product.get("IsFeatured") or product.get("isFeatured", False)
            is_new = product.get("IsNew") or product.get("isNew", False)
            created_at = product.get("CreatedAt") or product.get("createdAt")
            updated_at = product.get("UpdatedAt") or product.get("updatedAt")

            # Lấy CategoryID và tạo embedded category
            category_id_obj = None
            category_name = None
            
            # Thử lấy từ CategoryID field (có thể là ObjectId hoặc string)
            category_id_raw = product.get("CategoryID")
            if category_id_raw:
                # Convert sang string để tìm trong map
                category_id_str = str(category_id_raw)
                if category_id_str in category_map:
                    category_id_obj = category_map[category_id_str]["categoryId"]
                    category_name = category_map[category_id_str]["name"]
                else:
                    # Thử convert sang ObjectId và tìm lại
                    try:
                        if isinstance(category_id_raw, ObjectId):
                            category_id_str = str(category_id_raw)
                        else:
                            category_id_obj_temp = ObjectId(category_id_raw)
                            category_id_str = str(category_id_obj_temp)
                        
                        if category_id_str in category_map:
                            category_id_obj = category_map[category_id_str]["categoryId"]
                            category_name = category_map[category_id_str]["name"]
                    except Exception:
                        pass
            
            # Nếu chưa tìm thấy, thử lấy từ CategoryName và tìm ID
            if not category_id_obj:
                category_name = product.get("CategoryName") or product.get("categoryName")
                if category_name:
                    # Tìm category theo name
                    for cat_id_str, cat_data in category_map.items():
                        if cat_data["name"] == category_name:
                            category_id_obj = cat_data["categoryId"]
                            category_name = cat_data["name"]
                            break

            # Tạo embedded category object
            category_embedded = None
            if category_id_obj:
                # Đảm bảo categoryId là ObjectId
                if not isinstance(category_id_obj, ObjectId):
                    try:
                        category_id_obj = ObjectId(category_id_obj)
                    except Exception:
                        print(f"   ⚠️  Product {product_id}: Không thể convert CategoryID sang ObjectId")
                        category_id_obj = None
                
                if category_id_obj:
                    category_embedded = {
                        "categoryId": category_id_obj,
                        "name": category_name or ""
                    }
            
            if not category_embedded:
                # Nếu không có category, tạo empty category (required field)
                print(f"   ⚠️  Product {product_id}: Không tìm thấy category, tạo category rỗng")
                category_embedded = {
                    "categoryId": ObjectId(),
                    "name": ""
                }

            # Lấy BrandID và tạo embedded brand
            brand_id_obj = None
            brand_name = None
            
            # Thử lấy từ BrandID field (có thể là ObjectId hoặc string)
            brand_id_raw = product.get("BrandID")
            if brand_id_raw:
                # Convert sang string để tìm trong map
                brand_id_str = str(brand_id_raw)
                if brand_id_str in brand_map:
                    brand_id_obj = brand_map[brand_id_str]["brandId"]
                    brand_name = brand_map[brand_id_str]["name"]
                else:
                    # Thử convert sang ObjectId và tìm lại
                    try:
                        if isinstance(brand_id_raw, ObjectId):
                            brand_id_str = str(brand_id_raw)
                        else:
                            brand_id_obj_temp = ObjectId(brand_id_raw)
                            brand_id_str = str(brand_id_obj_temp)
                        
                        if brand_id_str in brand_map:
                            brand_id_obj = brand_map[brand_id_str]["brandId"]
                            brand_name = brand_map[brand_id_str]["name"]
                    except Exception:
                        pass
            
            # Nếu chưa tìm thấy, thử lấy từ BrandName hoặc Brand field
            if not brand_id_obj:
                brand_name = product.get("BrandName") or product.get("Brand") or product.get("brandName")
                if brand_name:
                    # Tìm brand theo name
                    for br_id_str, br_data in brand_map.items():
                        if br_data["name"] == brand_name:
                            brand_id_obj = br_data["brandId"]
                            brand_name = br_data["name"]
                            break

            # Tạo embedded brand object
            brand_embedded = None
            if brand_id_obj:
                # Đảm bảo brandId là ObjectId
                if not isinstance(brand_id_obj, ObjectId):
                    try:
                        brand_id_obj = ObjectId(brand_id_obj)
                    except Exception:
                        print(f"   ⚠️  Product {product_id}: Không thể convert BrandID sang ObjectId")
                        brand_id_obj = None
                
                if brand_id_obj:
                    brand_embedded = {
                        "brandId": brand_id_obj,
                        "name": brand_name or ""
                    }
            
            # Brand là optional, có thể để None nếu không tìm thấy
            if not brand_embedded and brand_name:
                print(f"   ⚠️  Product {product_id}: Brand name '{brand_name}' không tìm thấy ID, để brand = None")

            # Tạo update document với cấu trúc mới
            update_doc = {
                "$set": {
                    "productName": product_name,
                    "description": description,
                    "price": float(price) if price is not None else 0.0,
                    "stock": int(stock) if stock is not None else 0,
                    "status": status,
                }
            }

            # Thêm các field optional
            if original_price is not None:
                update_doc["$set"]["originalPrice"] = float(original_price)
            if image:
                update_doc["$set"]["image"] = image
            if rating is not None:
                update_doc["$set"]["rating"] = float(rating)
            if review_count is not None:
                update_doc["$set"]["reviewCount"] = int(review_count)
            if is_featured is not None:
                update_doc["$set"]["isFeatured"] = bool(is_featured)
            if is_new is not None:
                update_doc["$set"]["isNew"] = bool(is_new)
            if created_at:
                update_doc["$set"]["createdAt"] = created_at
            else:
                # Nếu không có createdAt, dùng thời gian hiện tại
                update_doc["$set"]["createdAt"] = datetime.utcnow()
            
            if updated_at:
                update_doc["$set"]["updatedAt"] = updated_at
            else:
                update_doc["$set"]["updatedAt"] = datetime.utcnow()

            # Thêm embedded category và brand (luôn có category, brand có thể None)
            update_doc["$set"]["category"] = category_embedded
            update_doc["$set"]["brand"] = brand_embedded if brand_embedded else None

            # Xóa các field cũ
            update_doc["$unset"] = {
                "ProductName": "",
                "Description": "",
                "Price": "",
                "OriginalPrice": "",
                "Stock": "",
                "Status": "",
                "Image": "",
                "Rating": "",
                "ReviewCount": "",
                "IsFeatured": "",
                "IsNew": "",
                "CreatedAt": "",
                "UpdatedAt": "",
                "CategoryID": "",
                "CategoryName": "",
                "BrandID": "",
                "BrandName": "",
                "Brand": "",
            }

            # Cập nhật product
            result = await products_collection.update_one(
                {"_id": product_id},
                update_doc
            )

            if result.modified_count > 0:
                migrated_count += 1
                if migrated_count <= 5:  # In 5 products đầu tiên để debug
                    print(f"   ✅ Migrated product {product_id}: {product_name}")
                    print(f"      Category: {category_embedded.get('name', 'N/A')} (ID: {category_embedded.get('categoryId', 'N/A')})")
                    if brand_embedded:
                        print(f"      Brand: {brand_embedded.get('name', 'N/A')} (ID: {brand_embedded.get('brandId', 'N/A')})")
                    else:
                        print("      Brand: None")
            else:
                updated_count += 1

            if migrated_count % 100 == 0:
                print(f"   📊 Đã migrate {migrated_count} products...")

        except Exception as e:
            print(f"   ❌ Lỗi khi migrate product {product.get('_id')}: {e}")
            import traceback
            traceback.print_exc()
            skipped_count += 1

    print(f"   ✅ Đã migrate {migrated_count} products, cập nhật {updated_count} products (đã có cấu trúc mới), bỏ qua {skipped_count} products")


async def test_connection(client: AsyncIOMotorClient, db_name: str) -> bool:
    """Test kết nối MongoDB"""
    try:
        await client.admin.command("ping")
        print("✅ Kết nối MongoDB thành công!")
        print(f"   Database: {db_name}")
        return True
    except Exception as e:
        print(f"❌ Không thể kết nối MongoDB: {e}")
        return False


async def try_multiple_ports(db_name: str) -> Optional[str]:
    """
    Thử kết nối với nhiều port phổ biến của MongoDB
    Returns: URI thành công hoặc None
    """
    common_ports = [27018, 27017, 27019]

    for port in common_ports:
        test_uri = f"mongodb://localhost:{port}/{db_name}"
        print(f"   🔄 Đang thử port {port}...")

        try:
            test_client = AsyncIOMotorClient(
                test_uri, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000
            )
            await test_client.admin.command("ping")
            test_client.close()
            print(f"   ✅ Tìm thấy MongoDB trên port {port}!")
            return test_uri
        except Exception:
            continue

    return None


async def main():
    """Hàm main để chạy migration"""
    print("=" * 60)
    print("🚀 BẮT ĐẦU MIGRATION: Gộp products, categories, brands")
    print("=" * 60)

    # Lấy MongoDB URI (tự động detect localhost hoặc Docker)
    mongodb_uri = get_mongodb_uri()
    db_name = settings.MONGODB_DB

    print("\n📡 Đang kết nối MongoDB...")
    # Ẩn password nếu có trong URI
    display_uri = mongodb_uri
    if "@" in mongodb_uri:
        parts = mongodb_uri.split("@")
        if len(parts) == 2:
            display_uri = f"{parts[0].split(':')[0]}:***@{parts[1]}"
    print(f"   URI: {display_uri}")
    print(f"   Database: {db_name}")

    # Kết nối database
    client = AsyncIOMotorClient(
        mongodb_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    db = client[db_name]

    # Test kết nối
    if not await test_connection(client, db_name):
        print("\n⚠️  Không thể kết nối với URI mặc định, đang thử các port khác...")

        # Thử các port phổ biến
        working_uri = await try_multiple_ports(db_name)

        if working_uri:
            print(f"\n✅ Tìm thấy MongoDB! Sử dụng: {working_uri}")
            client.close()
            # Tạo client mới với URI đúng
            client = AsyncIOMotorClient(
                working_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000
            )
            db = client[db_name]
            mongodb_uri = working_uri
        else:
            print(
                "\n❌ Không tìm thấy MongoDB trên các port phổ biến (27018, 27017, 27019)"
            )
            print("\n💡 Gợi ý:")
            print("   1. Đảm bảo MongoDB đang chạy: docker ps")
            print("   2. Kiểm tra port mapping trong docker-compose.yml")
            print("   3. Chỉ định URI thủ công: export MONGODB_URI='mongodb://localhost:27018/cosmetic_shop_db'")
            print("   4. Hoặc chạy: docker-compose up -d mongodb")
            client.close()
            sys.exit(1)

    try:
        # Kiểm tra xem đã migrate chưa
        if await check_migration_done(db):
            print("\n⚠️  Migration đã được chạy trước đó!")
            print("   💡 Để chạy lại, bạn cần xóa migration flag:")
            print("      db.migration_flags.deleteOne({name: 'products_embedded_migration_v1'})")
            response = input("Bạn có muốn xóa flag và chạy lại? (yes/no): ")
            if response.lower() == "yes":
                flag_collection = db[MIGRATION_FLAG_COLLECTION]
                await flag_collection.delete_one({"name": MIGRATION_FLAG_NAME})
                print("   ✅ Đã xóa migration flag, tiếp tục migration...")
            else:
                print("❌ Hủy migration")
                return

        print("\n📋 Bắt đầu migration...")
        print("   ⚠️  Lưu ý: Đảm bảo đã backup database trước khi chạy!")

        # Xác nhận
        response = input("\nBạn có chắc chắn muốn tiếp tục? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Hủy migration")
            return

        # Chạy migration
        await migrate_products(db)

        # Đánh dấu migration đã hoàn thành
        await mark_migration_done(db)

        print("\n" + "=" * 60)
        print("✅ MIGRATION HOÀN THÀNH!")
        print("=" * 60)
        print("\n📝 Tóm tắt:")
        print("   ✅ Đã gộp products, categories, brands thành collection products với embedded structure")
        print("   ✅ Đã chuyển đổi CategoryID -> category: {categoryId, name}")
        print("   ✅ Đã chuyển đổi BrandID -> brand: {brandId, name}")
        print("   ✅ Đã xóa các field cũ (ProductName, CategoryID, BrandID, ...)")
        print("\n⚠️  Lưu ý:")
        print("   - Collections categories và brands vẫn còn (có thể xóa sau khi kiểm tra)")
        print("   - Migration flag đã được đánh dấu, script sẽ không chạy lại tự động")

    except Exception as e:
        print(f"\n❌ LỖI KHI MIGRATION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

