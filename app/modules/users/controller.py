from typing import Optional
from app.modules.users.schemas import UserUpdate
from app.modules.users.model import User


async def get_user_by_account_id(account_id: str) -> Optional[User]:
    """Get user by AccountID"""
    return await User.find_one(User.AccountID == account_id)

# TUI COMMENT TẠM
# async def update_user_profile(
#     user: User, full_name: str = None, phone: str = None, address: str = None
# ) -> User:
#     """Update user profile information"""
#     if full_name is not None:
#         user.FullName = full_name
#     if phone is not None:
#         user.Phone = phone
#     if address is not None:
#         user.Address = address

#     await user.save()
#     return user

async def update_user_profile(user_id: str, data: UserUpdate) -> User | None:
    user = await User.get(user_id)
    if not user:
        return None

    if data.FullName is not None:
        user.FullName = data.FullName
    if data.Phone is not None:
        user.Phone = data.Phone
    if data.Address is not None:
        user.Address = data.Address

    await user.save()
    return user