from app.modules.shippers.model import Shipper
from app.modules.shippers.schemas import ShipperCreate, ShipperUpdate
from app.modules.auth.model import Account, Role
from fastapi import HTTPException, status
from app.modules.auth.controller import get_password_hash

# ------------------- SHIPPER CONTROLLER -------------------
async def create_shipper(data: ShipperCreate):
    email = data.Email.strip().lower()
    print(f"📩 Register new shipper\n\n\n: {email}")

    # Kiểm tra email trùng
    existing = await Account.find_one({"Email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Lấy role mặc định
    default_role = await Role.find_one({"RoleName": "Shipper"})
    if not default_role:
        default_role = Role(RoleName="Shipper")
        await default_role.insert()

    # Tạo Account
    account = Account(
        Email=email,
        PasswordHash=get_password_hash(data.Password),
        RoleID=str(default_role.id),
        Status="Active",
    )
    await account.insert()
    print(f"\n\n\nAccount created: {account.model_dump()}")

    shipper = Shipper(
        AccountID=account.id,
        FullName=data.FullName,
        Phone=data.Phone,
    )
    await shipper.insert()
    

    shipper_dict = {
        "AccountID": str(account.id),
        "ShipperID": str(shipper.id),
        "Email": email,
        "FullName": data.FullName,
        "Phone": data.Phone,
        "CreatedAt": shipper.CreatedAt,
        "UpdatedAt": shipper.UpdatedAt,
    }

    print(f"User dict trả về: {shipper_dict}")
    return shipper_dict


async def get_shipper(shipper_id: str) -> Shipper | None:
    return await Shipper.get(shipper_id)


async def list_shippers() -> list[Shipper]:
    return await Shipper.find_all().to_list()


async def update_shipper(shipper_id: str, data: ShipperUpdate) -> Shipper | None:
    shipper = await Shipper.get(shipper_id)
    if not shipper:
        return None

    if data.FullName is not None:
        shipper.FullName = data.FullName
    if data.Phone is not None:
        shipper.Phone = data.Phone

    await shipper.save()
    return shipper


async def delete_shipper(shipper_id: str) -> bool:
    shipper = await Shipper.get(shipper_id)
    if not shipper:
        return False

    await shipper.delete()
    return True
