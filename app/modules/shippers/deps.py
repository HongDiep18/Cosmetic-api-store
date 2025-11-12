from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_account
from app.modules.auth.model import Account


async def require_shipper_account(
    current_account: Account = Depends(get_current_account),
) -> Account:
    """
    Dependency yêu cầu tài khoản phải có vai trò "Shipper"
    """
    if not current_account or current_account.role.lower() != "shipper":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shipper privilege required",
        )

    return current_account
