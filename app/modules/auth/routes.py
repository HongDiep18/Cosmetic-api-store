from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import traceback


from app.core.deps import get_current_account, require_admin_account
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
    AccountOut,
)
from app.modules.auth.controller import (
    authenticate_user,
    change_password,
    forgot_password,
    register_user,
    reset_password,
    set_account_role,
    set_account_status,
    create_login_token,
)
from app.modules.auth.model import Account

router = APIRouter(tags=["Auth"])


# ------------------- PUBLIC ROUTES -------------------
@router.post("/register", response_model=AccountOut)
async def register(data: RegisterRequest):
    print("📩 Dữ liệu nhận được:", data.model_dump())

    try:
        # Gọi controller tạo tài khoản
        account_dict = await register_user(
            Email=data.Email,
            Password=data.Password,
            FullName=data.FullName,
            Phone=data.Phone,
            Address=data.Address,
        )

        print("🧾 Account dict trả về:", account_dict)

        # Validate output schema
        validated_account = AccountOut.model_validate(account_dict)
        return validated_account

    except Exception as e:
        print("❌ ValidationError chi tiết:")
        traceback.print_exc()
        return JSONResponse(
            status_code=400,
            content={
                "error": "Response model validation failed",
                "details": str(e),
            },
        )


@router.post("/login")
async def login_for_access_token(payload: LoginRequest):
    print("📩 Raw payload:", payload)

    account = await authenticate_user(payload.Email, payload.Password)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    print(f"🎭 Role name cho account {account.email}: {account.role}")
    access_token = create_login_token(account)
    return Token(AccessToken=access_token, RefreshToken=None)


@router.post("/forgot-password")
async def forgot_password_endpoint(data: ForgotPasswordRequest):
    message = await forgot_password(data.email)
    return {"message": message}


@router.post("/reset-password")
async def reset_password_endpoint(data: ResetPasswordRequest):
    message = await reset_password(data.token, data.newPassword)
    return {"message": message}


@router.post("/refresh-token", response_model=Token)
async def refresh_token(_: RefreshTokenRequest):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented",
    )


# ------------------- AUTH ROUTES -------------------


@router.get("/me", response_model=AccountOut)
async def read_me(current_account: Account = Depends(get_current_account)):
    if not current_account:
        raise HTTPException(status_code=404, detail="Account not found")

    print(f"✅ Found account: {current_account.profile.fullName}")
    return AccountOut.model_validate(current_account.model_dump())


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}


@router.patch("/change-password")
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    current_account: Account = Depends(get_current_account),
):
    await change_password(current_account, payload.currentPassword, payload.newPassword)
    return {"message": "Password updated"}


# ------------------- ADMIN ROUTES -------------------


# Role routes removed - roles are now embedded as strings in Account


@router.get(
    "/accounts",
    response_model=list[AccountOut],
    dependencies=[Depends(require_admin_account)],
)
async def list_accounts():
    accounts = await Account.find_all().to_list()
    return [AccountOut.model_validate(a.model_dump()) for a in accounts]


@router.get(
    "/accounts/{account_id}",
    response_model=AccountOut,
    dependencies=[Depends(require_admin_account)],
)
async def get_account_detail(account_id: str):
    account = await Account.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountOut.model_validate(account.model_dump())


@router.patch(
    "/accounts/{account_id}/status",
    response_model=AccountOut,
    # dependencies=[Depends(require_admin_account)],
)
async def update_account_status(account_id: str, payload: dict):
    status_value = payload.get("status")
    if not status_value:
        raise HTTPException(status_code=400, detail="status is required")

    account = await set_account_status(account_id, status_value)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountOut.model_validate(account.model_dump())


@router.patch(
    "/accounts/{account_id}/role",
    response_model=AccountOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_account_role(account_id: str, payload: dict):
    role_name = payload.get("role") or payload.get("RoleName")
    if not role_name:
        raise HTTPException(status_code=400, detail="role is required")

    account = await set_account_role(account_id, role_name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountOut.model_validate(account.model_dump())
