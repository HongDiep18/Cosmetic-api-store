from typing import Optional
from app.modules.users.schemas import UserUpdate
from beanie import Document, PydanticObjectId

from app.modules.users.model import User
from fastapi import HTTPException, status
from beanie import PydanticObjectId
from bson import ObjectId


async def get_user_by_account_id(account_id: str) -> Optional[User]:
    """Get user by AccountID"""
    return await User.find_one(User.AccountID == account_id)




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

