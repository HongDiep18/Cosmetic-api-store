from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_account
from app.modules.auth.model import Account
from app.modules.users.model import User
from app.modules.users.schemas import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def read_users_me(current_account: Account = Depends(get_current_account)):
    user = await User.find_one(User.AccountID == str(current_account.AccountID))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )
    return UserOut.model_validate(user, from_attributes=True)
