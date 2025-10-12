from typing import Optional

from app.modules.users.model import User


async def get_user_by_account_id(account_id: str) -> Optional[User]:
    """Get user by AccountID"""
    return await User.find_one(User.AccountID == account_id)


async def update_user_profile(
    user: User, full_name: str = None, phone: str = None, address: str = None
) -> User:
    """Update user profile information"""
    if full_name is not None:
        user.FullName = full_name
    if phone is not None:
        user.Phone = phone
    if address is not None:
        user.Address = address

    await user.save()
    return user
