# -*- coding: utf-8 -*-

#!/usr/bin/env python3
"""
Script để làm sạch database và tạo lại cấu trúc đúng
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import models
from app.modules.auth.model import Account, Role
from app.modules.users.model import User


async def clean_and_recreate_database():
    """Làm sạch database và tạo lại cấu trúc đúng"""

    # Kết nối MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27018")
    database = client.cosmetic_delivery_db  # Thay đổi tên database nếu cần

    # Khởi tạo Beanie
    await init_beanie(database=database, document_models=[Account, Role, User])

    print("=== LÀM SẠCH VÀ TẠO LẠI DATABASE ===\n")

    # Xác nhận từ user
    print("⚠️  CẢNH BÁO: Script này sẽ xóa tất cả dữ liệu hiện tại!")
    print("Đảm bảo bạn đã backup dữ liệu quan trọng trước khi tiếp tục.")
    print()

    confirm = input("Bạn có chắc chắn muốn tiếp tục? (yes/no): ")
    if confirm.lower() != "yes":
        print("Hủy bỏ thao tác.")
        return

    try:
        # Xóa các collection cũ
        print("1. Xóa các collection cũ...")
        await database.users.drop()
        print("   ✅ Đã xóa collection 'users'")

        await database.accounts.drop()
        print("   ✅ Đã xóa collection 'accounts'")

        await database.roles.drop()
        print("   ✅ Đã xóa collection 'roles'")

        # Tạo role mặc định
        print("\n2. Tạo role mặc định...")
        default_role = Role(RoleName="User")
        await default_role.insert()
        print(f"   ✅ Đã tạo role 'User' với ID: {default_role.RoleID}")

        admin_role = Role(RoleName="Admin")
        await admin_role.insert()
        print(f"   ✅ Đã tạo role 'Admin' với ID: {admin_role.RoleID}")

        print("\n3. ✅ HOÀN THÀNH!")
        print("   - Database đã được làm sạch")
        print("   - Cấu trúc mới đã được tạo")
        print("   - Bạn có thể đăng ký lại từ frontend")

    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        print("Vui lòng kiểm tra kết nối MongoDB và thử lại.")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(clean_and_recreate_database())
