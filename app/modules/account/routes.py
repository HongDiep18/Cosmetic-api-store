
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import require_admin_account
from app.modules.account.controller import (
    get_account_custom,
)
from app.modules.account.schemas import (
    AccountOut
)

router = APIRouter(tags=["Admin Account View"])

# ------------------- ADMIN ROUTES -------------------
@router.get("/accountview/accounts",
            response_model=list[AccountOut],
            )
async def list_account():
    Account  = await get_account_custom()
    return Account



    

