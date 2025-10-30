# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Script để kiểm tra cấu trúc database và đưa ra khuyến nghị
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Import models
from app.modules.auth.model import Account, Role
from app.modules.users.model import User


async def check_database_structure():
    """Kiểm tra cấu trúc database và đưa ra khuyến nghị"""

    # Kết nối MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27018")
    database = client.cosmetic_shop_db  # Thay đổi tên database nếu cần

    # Khởi tạo Beanie
    await init_beanie(database=database, document_models=[Account, Role, User])

    print("=== KIỂM TRA CẤU TRÚC DATABASE ===\n")

    # Kiểm tra collection users
    print("1. KIỂM TRA COLLECTION 'users':")
    users_collection = database.users
    users_count = await users_collection.count_documents({})
    print(f"   - Tổng số documents: {users_count}")

    if users_count > 0:
        # Lấy một document mẫu
        sample_user = await users_collection.find_one({})
        print(f"   - Các fields trong document mẫu: {list(sample_user.keys())}")

        # Kiểm tra field có vấn đề
        problematic_fields = []
        if "PasswordHash" in sample_user:
            problematic_fields.append("PasswordHash")
        if "Email" in sample_user:
            problematic_fields.append("Email")
        if "AccountID" in sample_user:
            problematic_fields.append("PasswordHash")

        if problematic_fields:
            print(
                f"   ⚠️  CẢNH BÁO: Tìm thấy các field không đúng schema: {problematic_fields}"
            )
            print(
                "   → Các field này nên ở trong collection 'accounts', không phải 'users'"
            )
        else:
            print("    Cấu trúc collection 'users' đúng")

    print()

    # Kiểm tra collection accounts
    print("2. KIỂM TRA COLLECTION 'accounts':")
    accounts_collection = database.accounts
    accounts_count = await accounts_collection.count_documents({})
    print(f"   - Tổng số documents: {accounts_count}")

    if accounts_count > 0:
        sample_account = await accounts_collection.find_one({})
        print(f"   - Các fields trong document mẫu: {list(sample_account.keys())}")

        required_fields = ["Email", "PasswordHash", "RoleID", "Status"]
        missing_fields = [
            field for field in required_fields if field not in sample_account
        ]

        if missing_fields:
            print(f"   ⚠️  CẢNH BÁO: Thiếu các field bắt buộc: {missing_fields}")
        else:
            print("    Cấu trúc collection 'accounts' đúng")

    print()

    # Kiểm tra collection roles
    print("3. KIỂM TRA COLLECTION 'roles':")
    roles_collection = database.roles
    roles_count = await roles_collection.count_documents({})
    print(f"   - Tổng số documents: {roles_count}")

    if roles_count > 0:
        sample_role = await roles_collection.find_one({})
        print(f"   - Các fields trong document mẫu: {list(sample_role.keys())}")

    print()

    # Đưa ra khuyến nghị
    print("=== KHUYẾN NGHỊ ===")

    if users_count > 0 and "PasswordHash" in (
        await users_collection.find_one({}) or {}
    ):
        print("1. ⚠️  PHÁT HIỆN DỮ LIỆU KHÔNG ĐÚNG CẤU TRÚC")
        print("   - Collection 'users' chứa field 'PasswordHash'")
        print("   - Điều này không đúng với schema hiện tại")
        print("   - Khuyến nghị: Xóa collection 'users' cũ và đăng ký lại")
        print("   - Hoặc migrate dữ liệu sang cấu trúc mới")
        print()
        print("2. ĐỂ SỬA LỖI:")
        print("   a) Xóa collection 'users' hiện tại:")
        print("      await database.users.drop()")
        print("   b) Đăng ký lại từ frontend")
        print("   c) Hoặc tạo script migrate dữ liệu")

    if accounts_count == 0 and users_count > 0:
        print("1. ⚠️  THIẾU COLLECTION 'accounts'")
        print("   - Có dữ liệu users nhưng không có accounts")
        print("   - Cần tạo lại cấu trúc đúng")

    if roles_count == 0:
        print("1. ⚠️  THIẾU COLLECTION 'roles'")
        print("   - Cần tạo role mặc định 'User'")

    print("\n=== HOÀN THÀNH KIỂM TRA ===")


if __name__ == "__main__":
    asyncio.run(check_database_structure())
