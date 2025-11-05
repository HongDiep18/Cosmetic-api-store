from fastapi import Depends, HTTPException, status
from beanie import PydanticObjectId
from app.core.deps import get_current_account
from app.modules.auth.model import Account, Role
from app.modules.shippers.model import Shipper


async def require_shipper_account(
    current_account: Account = Depends(get_current_account),
) -> Shipper:
    """
    Dependency yêu cầu tài khoản phải có vai trò "Shipper"
    VÀ trả về hồ sơ (profile) Shipper tương ứng.
    """
    role = await Role.get(current_account.RoleID)
    if not role or role.RoleName.lower() != "shipper":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shipper privilege required",
        )

    shipper_profile = await Shipper.find_one(
        Shipper.AccountID == PydanticObjectId(current_account.id)
    )

    if not shipper_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipper profile not found for this account",
        )

    return shipper_profile
