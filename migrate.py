"""
Script Migration: Gộp accounts, users, shippers, roles thành 1 collection Account
Chạy script này CHỈ MỘT LẦN để di chuyển dữ liệu từ cấu trúc cũ sang cấu trúc mới.

Cấu trúc cũ:
- accounts: AccountID, Email, PasswordHash, RoleID, Status, ...
- users: UserID, AccountID, FullName, Phone, Address, ...
- shippers: ShipperID, AccountID, FullName, Phone, ...
- roles: RoleID, RoleName, ...

Cấu trúc mới:
- accounts: _id, email, passwordHash, role, status, profile: {fullName, phone, address}, ...

Usage:
    python migrate.py
"""

# python E:/Subject/No_SQL/Web_NoSQL/react-cosmetic-api/migrate.py
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
        # Nếu docker-compose.yml có "27018:27017", thì host dùng 27018
        local_uri_27018 = f"mongodb://localhost:27018/{db_name}"
        print("⚠️  Phát hiện Docker hostname 'mongodb'")
        print("   Thử kết nối với localhost:27018 (port mapping phổ biến trong Docker)")
        return local_uri_27018

    return default_uri


# Flag để đảm bảo chỉ chạy một lần
MIGRATION_FLAG_COLLECTION = "migration_flags"
MIGRATION_FLAG_NAME = "accounts_unified_migration_v1"


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
            "description": "Gộp accounts, users, shippers, roles thành 1 collection Account",
        }
    )


async def migrate_accounts(db):
    """
    Bước 1: Gộp accounts, users, shippers, roles thành collection accounts mới
    """
    print("🔄 Bước 1: Đang gộp accounts, users, shippers, roles...")

    # Kiểm tra xem đã có accounts_new chưa (migration bị gián đoạn)
    accounts_new_collection = db["accounts_new"]
    accounts_new_count = await accounts_new_collection.count_documents({})

    if accounts_new_count > 0:
        print(
            f"   ⚠️  Phát hiện collection 'accounts_new' với {accounts_new_count} documents"
        )
        print("   📋 Migration có thể đã bị gián đoạn, đang tiếp tục...")

        # Kiểm tra xem collection accounts cũ có tồn tại không
        accounts_collection = db["accounts"]
        old_accounts_count = await accounts_collection.count_documents({})

        if old_accounts_count > 0:
            # Backup collection cũ nếu chưa backup
            backup_count = await db["accounts_backup"].count_documents({})
            if backup_count == 0:
                print("   💾 Đang backup collection accounts cũ...")
                old_accounts = await accounts_collection.find({}).to_list(length=None)
                if old_accounts:
                    await db["accounts_backup"].insert_many(old_accounts)

            # Xóa collection cũ
            print("   🗑️  Đang xóa collection accounts cũ...")
            await accounts_collection.drop()

        # Rename accounts_new thành accounts
        print("   🔄 Đang đổi tên accounts_new thành accounts...")
        try:
            # Sử dụng command để rename collection trong Motor
            await db.command(
                {
                    "renameCollection": f"{db.name}.accounts_new",
                    "to": f"{db.name}.accounts",
                    "dropTarget": True,  # Xóa collection đích nếu đã tồn tại
                }
            )
        except Exception as e:
            # Nếu lỗi vì collection đích không tồn tại, thử không có dropTarget
            error_msg = str(e).lower()
            if "target namespace" in error_msg or "already exists" in error_msg:
                # Collection accounts đã tồn tại, xóa nó trước
                print("   ⚠️  Collection accounts đã tồn tại, đang xóa...")
                await db["accounts"].drop()
                await db.command(
                    {
                        "renameCollection": f"{db.name}.accounts_new",
                        "to": f"{db.name}.accounts",
                    }
                )
            else:
                raise
        print("   ✅ Hoàn thành Bước 1 (tiếp tục từ migration trước)!")
        return

    # Nếu chưa có accounts_new, thực hiện migration từ đầu
    accounts_collection = db["accounts"]
    users_collection = db["users"]
    shippers_collection = db["shippers"]
    roles_collection = db["roles"]

    # Lấy tất cả dữ liệu từ collections cũ
    old_accounts = await accounts_collection.find({}).to_list(length=None)
    old_users = await users_collection.find({}).to_list(length=None)
    old_shippers = await shippers_collection.find({}).to_list(length=None)
    old_roles = await roles_collection.find({}).to_list(length=None)

    print(
        f"   📊 Tìm thấy: {len(old_accounts)} accounts, {len(old_users)} users, {len(old_shippers)} shippers, {len(old_roles)} roles"
    )

    # Tạo mapping RoleID -> RoleName
    role_map: Dict[str, str] = {}
    for role in old_roles:
        role_id = str(role.get("_id", ""))
        role_name = role.get("RoleName", "")
        if role_id and role_name:
            role_map[role_id] = role_name

    # Tạo mapping AccountID -> User
    user_map: Dict[str, Dict[str, Any]] = {}
    for user in old_users:
        account_id = str(user.get("AccountID", ""))
        if account_id:
            user_map[account_id] = {
                "FullName": user.get("FullName", ""),
                "Phone": user.get("Phone", ""),
                "Address": user.get("Address", ""),
            }

    # Tạo mapping AccountID -> Shipper
    shipper_map: Dict[str, Dict[str, Any]] = {}
    for shipper in old_shippers:
        account_id = str(shipper.get("AccountID", ""))
        if account_id:
            shipper_map[account_id] = {
                "FullName": shipper.get("FullName", ""),
                "Phone": shipper.get("Phone", ""),
            }

    # Tạo collection mới (tạm thời)
    new_accounts_collection = db["accounts_new"]

    migrated_count = 0
    skipped_count = 0

    for old_account in old_accounts:
        try:
            account_id = old_account.get("_id")
            if not account_id:
                skipped_count += 1
                continue

            # Lấy RoleName
            role_id = str(old_account.get("RoleID", ""))
            role_name = role_map.get(role_id, "User")  # Default là User

            # Lấy profile từ User hoặc Shipper
            profile_data = None
            if role_name == "User":
                user_data = user_map.get(str(account_id))
                if user_data:
                    profile_data = {
                        "fullName": user_data.get("FullName", ""),
                        "phone": user_data.get("Phone", ""),
                        "address": user_data.get("Address"),
                    }
            elif role_name == "Shipper":
                shipper_data = shipper_map.get(str(account_id))
                if shipper_data:
                    profile_data = {
                        "fullName": shipper_data.get("FullName", ""),
                        "phone": shipper_data.get("Phone", ""),
                        "address": None,  # Shipper không có address
                    }
            elif role_name == "Admin":
                # Admin có thể không có trong users/shippers, tạo profile mặc định
                profile_data = {
                    "fullName": "Admin",
                    "phone": old_account.get("Phone", ""),
                    "address": None,
                }

            # Nếu không tìm thấy profile, bỏ qua
            if not profile_data:
                print(
                    f"   ⚠️  Không tìm thấy profile cho account {account_id}, role: {role_name}"
                )
                skipped_count += 1
                continue

            # Tạo document mới
            new_account = {
                "_id": account_id,
                "email": old_account.get("Email", "").lower(),
                "passwordHash": old_account.get("PasswordHash", ""),
                "role": role_name,
                "status": old_account.get("Status", "Active"),
                "profile": profile_data,
                "passwordResetToken": old_account.get("PasswordResetToken"),
                "passwordResetExpires": old_account.get("PasswordResetExpires"),
                "createdAt": old_account.get("CreatedAt", datetime.utcnow()),
                "updatedAt": old_account.get("UpdatedAt", datetime.utcnow()),
            }

            # Insert vào collection mới
            await new_accounts_collection.insert_one(new_account)
            migrated_count += 1

        except Exception as e:
            print(f"   ❌ Lỗi khi migrate account {old_account.get('_id')}: {e}")
            skipped_count += 1

    print(
        f"   ✅ Đã migrate {migrated_count} accounts, bỏ qua {skipped_count} accounts"
    )

    if migrated_count > 0:
        # Backup collection cũ và thay thế bằng collection mới
        print("   💾 Đang backup collection cũ...")
        # Kiểm tra xem đã backup chưa
        backup_count = await db["accounts_backup"].count_documents({})
        if backup_count == 0:
            await db["accounts_backup"].insert_many(old_accounts)
        else:
            print("   ℹ️  Collection đã được backup trước đó, bỏ qua")

        print("   🔄 Đang thay thế collection accounts...")
        # Kiểm tra xem collection accounts cũ có tồn tại không
        try:
            old_count = await accounts_collection.count_documents({})
            if old_count > 0:
                await accounts_collection.drop()
        except Exception:
            pass  # Collection có thể đã bị xóa

        # Rename accounts_new thành accounts
        try:
            # Sử dụng command để rename collection trong Motor
            await db.command(
                {
                    "renameCollection": f"{db.name}.accounts_new",
                    "to": f"{db.name}.accounts",
                    "dropTarget": True,  # Xóa collection đích nếu đã tồn tại
                }
            )
        except Exception as e:
            # Nếu lỗi vì collection đích không tồn tại, thử không có dropTarget
            error_msg = str(e).lower()
            if "target namespace" in error_msg or "already exists" in error_msg:
                # Collection accounts đã tồn tại, xóa nó trước
                print("   ⚠️  Collection accounts đã tồn tại, đang xóa và thay thế...")
                await accounts_collection.drop()
                await db.command(
                    {
                        "renameCollection": f"{db.name}.accounts_new",
                        "to": f"{db.name}.accounts",
                    }
                )
            else:
                raise

        print("   ✅ Hoàn thành Bước 1!")
    else:
        print("   ⚠️  Không có accounts nào được migrate, bỏ qua bước này")


async def migrate_orders(db):
    """
    Bước 2: Cập nhật Orders.UserID để trỏ đến Account._id
    """
    print("\n🔄 Bước 2: Đang cập nhật Orders.UserID...")

    orders_collection = db["orders"]
    users_collection = db["users"]

    # Tạo mapping UserID -> AccountID
    user_to_account_map: Dict[str, str] = {}
    old_users = await users_collection.find({}).to_list(length=None)
    for user in old_users:
        user_id = str(user.get("_id", ""))
        account_id = str(user.get("AccountID", ""))
        if user_id and account_id:
            user_to_account_map[user_id] = account_id

    print(f"   📊 Tìm thấy {len(user_to_account_map)} mappings UserID -> AccountID")

    # Cập nhật tất cả orders
    orders = await orders_collection.find({}).to_list(length=None)
    updated_count = 0
    skipped_count = 0

    for order in orders:
        try:
            order_id = order.get("_id")
            old_user_id = order.get("UserID")

            if not old_user_id:
                skipped_count += 1
                continue

            # Tìm AccountID tương ứng
            old_user_id_str = str(old_user_id)
            account_id = user_to_account_map.get(old_user_id_str)

            if account_id:
                # Cập nhật UserID thành AccountID
                await orders_collection.update_one(
                    {"_id": order_id}, {"$set": {"UserID": ObjectId(account_id)}}
                )
                updated_count += 1
            else:
                print(f"   ⚠️  Không tìm thấy AccountID cho UserID {old_user_id_str}")
                skipped_count += 1

        except Exception as e:
            print(f"   ❌ Lỗi khi cập nhật order {order.get('_id')}: {e}")
            skipped_count += 1

    print(f"   ✅ Đã cập nhật {updated_count} orders, bỏ qua {skipped_count} orders")
    print("   ✅ Hoàn thành Bước 2!")


async def migrate_shipments(db):
    """
    Bước 3: Cập nhật Shipments.ShipperID để trỏ đến Account._id
    """
    print("\n🔄 Bước 3: Đang cập nhật Shipments.ShipperID...")

    shipments_collection = db["shipments"]
    shippers_collection = db["shippers"]

    # Tạo mapping ShipperID -> AccountID
    shipper_to_account_map: Dict[str, str] = {}
    old_shippers = await shippers_collection.find({}).to_list(length=None)
    for shipper in old_shippers:
        shipper_id = str(shipper.get("_id", ""))
        account_id = str(shipper.get("AccountID", ""))
        if shipper_id and account_id:
            shipper_to_account_map[shipper_id] = account_id

    print(
        f"   📊 Tìm thấy {len(shipper_to_account_map)} mappings ShipperID -> AccountID"
    )

    # Cập nhật tất cả shipments
    shipments = await shipments_collection.find({}).to_list(length=None)
    updated_count = 0
    skipped_count = 0

    for shipment in shipments:
        try:
            shipment_id = shipment.get("_id")
            old_shipper_id = shipment.get("ShipperID")

            if not old_shipper_id:
                skipped_count += 1
                continue

            # Tìm AccountID tương ứng
            old_shipper_id_str = str(old_shipper_id)
            account_id = shipper_to_account_map.get(old_shipper_id_str)

            if account_id:
                # Cập nhật ShipperID thành AccountID
                await shipments_collection.update_one(
                    {"_id": shipment_id}, {"$set": {"ShipperID": ObjectId(account_id)}}
                )
                updated_count += 1
            else:
                print(
                    f"   ⚠️  Không tìm thấy AccountID cho ShipperID {old_shipper_id_str}"
                )
                skipped_count += 1

        except Exception as e:
            print(f"   ❌ Lỗi khi cập nhật shipment {shipment.get('_id')}: {e}")
            skipped_count += 1

    print(
        f"   ✅ Đã cập nhật {updated_count} shipments, bỏ qua {skipped_count} shipments"
    )
    print("   ✅ Hoàn thành Bước 3!")


async def cleanup_old_collections(db):
    """
    Bước 4 (Tùy chọn): Xóa các collections cũ nếu muốn
    Lưu ý: Bước này sẽ XÓA VĨNH VIỄN dữ liệu cũ, chỉ chạy khi chắc chắn migration thành công
    """
    print("\n⚠️  Bước 4: Cleanup collections cũ (TÙY CHỌN)")
    print("   ⚠️  CẢNH BÁO: Bước này sẽ XÓA collections users, shippers, roles!")

    response = input("   Bạn có muốn xóa collections cũ? (yes/no): ")
    if response.lower() == "yes":
        try:
            await db["users"].drop()
            await db["shippers"].drop()
            await db["roles"].drop()
            print("   ✅ Đã xóa collections cũ")
        except Exception as e:
            print(f"   ❌ Lỗi khi xóa collections: {e}")
    else:
        print("   ⏭️  Bỏ qua cleanup, giữ nguyên collections cũ")


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
    print("🚀 BẮT ĐẦU MIGRATION: Gộp accounts, users, shippers, roles")
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
        serverSelectionTimeoutMS=5000,  # Timeout ngắn hơn để fail fast
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
            print(
                "   2. Kiểm tra port mapping trong docker-compose.yml (hiện tại: 27018:27017)"
            )
            print(
                "   3. Chỉ định URI thủ công: export MONGODB_URI='mongodb://localhost:27018/cosmetic_shop_db'"
            )
            print("   4. Hoặc chạy: docker-compose up -d mongodb")
            client.close()
            sys.exit(1)

    try:
        # Kiểm tra xem đã migrate chưa
        if await check_migration_done(db):
            print("\n⚠️  Migration đã được chạy trước đó!")
            response = input("Bạn có muốn chạy lại? (yes/no): ")
            if response.lower() != "yes":
                print("❌ Hủy migration")
                return

        print("\n📋 Bắt đầu migration...")
        print("   ⚠️  Lưu ý: Đảm bảo đã backup database trước khi chạy!")

        # Xác nhận
        response = input("\nBạn có chắc chắn muốn tiếp tục? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Hủy migration")
            return

        # Chạy các bước migration
        await migrate_accounts(db)
        await migrate_orders(db)
        await migrate_shipments(db)

        # Đánh dấu migration đã hoàn thành
        await mark_migration_done(db)

        print("\n" + "=" * 60)
        print("✅ MIGRATION HOÀN THÀNH!")
        print("=" * 60)
        print("\n📝 Tóm tắt:")
        print(
            "   ✅ Đã gộp accounts, users, shippers, roles thành collection accounts mới"
        )
        print("   ✅ Đã cập nhật Orders.UserID -> Account._id")
        print("   ✅ Đã cập nhật Shipments.ShipperID -> Account._id")
        print("   ✅ Collection cũ đã được backup vào 'accounts_backup'")
        print("\n⚠️  Lưu ý:")
        print(
            "   - Collections users, shippers, roles vẫn còn (có thể xóa sau khi kiểm tra)"
        )
        print("   - Collection accounts_backup chứa backup dữ liệu cũ")
        print("   - Migration flag đã được đánh dấu, script sẽ không chạy lại tự động")

        # Hỏi có muốn cleanup không
        await cleanup_old_collections(db)

    except Exception as e:
        print(f"\n❌ LỖI KHI MIGRATION: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
