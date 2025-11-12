from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_account
from app.modules.auth.model import Account
from app.modules.auth.schemas import AccountOut
from app.modules.users.schemas import UserUpdate
from app.modules.users.controller import update_user_profile

router = APIRouter()


@router.get("/me", response_model=AccountOut)
async def read_users_me(current_account: Account = Depends(get_current_account)):
    if not current_account or current_account.role != "User":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )
    return AccountOut.model_validate(current_account.model_dump())


@router.patch(
    "/{account_id}",
    response_model=AccountOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_user_endpoint(account_id: str, data: UserUpdate):
    account = await update_user_profile(account_id, data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return AccountOut.model_validate(account.model_dump())
