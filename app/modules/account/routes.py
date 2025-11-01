
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import require_admin_account
from app.modules.account.controller import (
    get_account_custom,
)
from app.modules.account.schemas import (
    AccountViewOut
)

router = APIRouter(tags=["Account"])

# ------------------- ADMIN ROUTES -------------------
@router.get("",
            response_model=list[AccountViewOut],
            )
async def list_account():
    Account  = await get_account_custom()
    return Account



    

