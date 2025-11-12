from app.modules.shippers.schemas import ShipperCreate, ShipperUpdate
from app.modules.auth.model import Account, Profile
from fastapi import HTTPException
from app.core.security import get_passwordHash


async def create_account_shipper(data: ShipperCreate):
    email = data.Email.strip().lower()
    print(f"📩 Register new shipper: {email}")

    # Kiểm tra email trùng
    existing = await Account.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Tạo Account với profile nhúng
    profile = Profile(
        fullName=data.FullName,
        phone=data.Phone,
        address=None,  # Shipper không có address
    )

    account = Account(
        email=email,
        passwordHash=get_passwordHash(data.Password),
        role="Shipper",
        status="Active",
        profile=profile,
    )
    await account.insert()
    print(f"Account created: {account.model_dump()}")

    account_dict = {
        "_id": str(account.id),
        "email": email,
        "role": "Shipper",
        "status": "Active",
        "profile": {
            "fullName": data.FullName,
            "phone": data.Phone,
        },
        "createdAt": account.createdAt,
        "updatedAt": account.updatedAt,
    }

    print(f"Shipper dict trả về: {account_dict}")
    return account_dict


async def get_shipper(account_id: str) -> Account | None:
    account = await Account.get(account_id)
    if account and account.role == "Shipper":
        return account
    return None


async def list_shippers() -> list[Account]:
    return await Account.find(Account.role == "Shipper").to_list()


async def update_shipper(account_id: str, data: ShipperUpdate) -> Account | None:
    account = await Account.get(account_id)
    if not account or account.role != "Shipper":
        return None

    if data.FullName is not None:
        account.profile.fullName = data.FullName
    if data.Phone is not None:
        account.profile.phone = data.Phone

    await account.save()
    return account


async def delete_shipper(account_id: str) -> bool:
    account = await Account.get(account_id)
    if not account:
        return False

    await account.delete()
    return True
