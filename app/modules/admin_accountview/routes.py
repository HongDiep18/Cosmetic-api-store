
# app/modules/admin_accountview/routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import require_admin_account
from app.modules.admin_accountview.controller import (
    get_account_custom
)
from app.modules.admin_accountview.schemas import (
    AccountOut
)


@router.get("/accountview/accounts",
            response_model=list[AccountOut],
            )
async def list_account():
    Account  = await get_account_custom()
    return Account
