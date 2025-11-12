from typing import Optional
from app.modules.users.schemas import UserUpdate
from app.modules.auth.model import Account


async def get_user_by_account_id(account_id: str) -> Optional[Account]:
    """Get user by AccountID"""
    account = await Account.get(account_id)
    if account and account.role == "User":
        return account
    return None


async def update_user_profile(account_id: str, data: UserUpdate) -> Account | None:
    account = await Account.get(account_id)
    if not account or account.role != "User":
        return None

    if data.FullName is not None:
        account.profile.fullName = data.FullName
    if data.Phone is not None:
        account.profile.phone = data.Phone
    if data.Address is not None:
        account.profile.address = data.Address

    await account.save()
    return account
