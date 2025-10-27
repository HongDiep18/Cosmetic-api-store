from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import traceback

from pydantic import ValidationError

from app.core.deps import get_current_account, require_admin_account
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
    RoleCreate,
    RoleOut,
    AccountOut,
)
from app.modules.auth.controller import (
    authenticate_user,
    change_password,
    create_login_token,
    forgot_password,
    register_user,
    reset_password,
    set_account_role,
    set_account_status,
)
from app.modules.users.schemas import UserOut
from app.modules.auth.model import Account, Role
from app.modules.users.model import User
from bson import ObjectId
router = APIRouter(tags=["Auth"])

# ------------------- PUBLIC ROUTES -------------------
@router.post("/register", response_model=UserOut)
async def register(data: RegisterRequest):
    print("📩 Dữ liệu nhận được:", data.model_dump())

    try:
        # Gọi controller tạo tài khoản + user
        user = await register_user(
            Email=data.Email,
            Password=data.Password,
            FullName=data.FullName,
            Phone=data.Phone,
            Address=data.Address,
        )

        # Convert user sang dict
        if hasattr(user, "to_dict"):
            user_dict = user.to_dict()
        elif hasattr(user, "model_dump"):
            user_dict = user.model_dump()
        elif isinstance(user, dict):
            user_dict = user
        else:
            raise TypeError(f"❌ Không biết cách convert kiểu {type(user)} sang dict")

        print("🧾 User dict trả về:", user_dict)

        # Validate output schema
        validated_user = UserOut.model_validate(user_dict)
        return validated_user

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



@router.post("/auth/login", response_model=Token)
async def login_for_access_token(payload: LoginRequest):
    print("📩 Raw payload:", payload)

    account, user = await authenticate_user(payload.Email, payload.Password)

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    role = await Role.get(account.RoleID)
    role_name = role.RoleName if role else "User"
    access_token = await create_login_token(account, role_name)
    # NOTE: refresh token flow not fully implemented; return None for now
    return Token(access_token=access_token, refresh_token=None)

    access_token = create_login_token(account, role_name)
    return Token(AccessToken=access_token, RefreshToken=None)

@router.post("/auth/forgot-password")
async def forgot_password_endpoint(data: ForgotPasswordRequest):
    """
    Request password reset. Always returns success message for security.
    """
    message = await forgot_password(data.email)
    return {"message": message}


@router.post("/auth/reset-password")
async def reset_password_endpoint(data: ResetPasswordRequest):
    """
    Reset password using token from email.
    """
    message = await reset_password(data.token, data.newPassword)
    return {"message": message}


@router.post("/auth/refresh-token", response_model=Token)
async def refresh_token(_: RefreshTokenRequest):
    # TODO: implement refresh token store/rotation; no-op for now
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented",
    )


# Authenticated routes
@router.get("/auth/me", response_model=UserOut)
async def read_me(current_account: Account = Depends(get_current_account)):
    print("🔐 Current account ID:", current_account.id)

    user = await User.find_one(User.AccountID == ObjectId(current_account.id))
    if not user:
        print("❌ Không tìm thấy user với AccountID:", current_account.id)
        raise HTTPException(status_code=404, detail="User not found")

    print("✅ Tìm thấy user:", user.FullName)
    user_dict = user.to_dict() if hasattr(user, "to_dict") else user.dict()
    return UserOut.model_validate(user_dict)


@router.post("/auth/logout")
async def logout():
    # TODO: invalidate refresh token; no-op
    return {"message": "Logged out"}


@router.patch("/auth/change-password")
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    current_account: Account = Depends(get_current_account),
):
    await change_password(current_account, payload.currentPassword, payload.newPassword)
    return {"message": "Password updated"}


# Admin - Roles
@router.post(
    "/roles", response_model=RoleOut, dependencies=[Depends(require_admin_account)]
)
async def create_role(payload: RoleCreate):
    role = Role(RoleName=payload.RoleName)
    await role.insert()
    return RoleOut.model_validate(role, from_attributes=True)


@router.get(
    "/roles",
    response_model=list[RoleOut],
    dependencies=[Depends(require_admin_account)],
)
async def list_roles():
    roles = await Role.find_all().to_list()
    return [RoleOut.model_validate(r, from_attributes=True) for r in roles]


@router.put(
    "/roles/{role_id}",
    response_model=RoleOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_role(role_id: str, payload: RoleCreate):
    role = await Role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    role.RoleName = payload.RoleName
    await role.save()
    return RoleOut.model_validate(role, from_attributes=True)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_account)],
)
async def delete_role(role_id: str):
    role = await Role.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    await role.delete()
    return None


# Admin - Accounts
@router.get(
    "/accounts",
    response_model=list[AccountOut],
    dependencies=[Depends(require_admin_account)],
)
async def list_accounts():
    accounts = await Account.find_all().to_list()
    return [AccountOut.model_validate(a, from_attributes=True) for a in accounts]


@router.get(
    "/accounts/{account_id}",
    response_model=AccountOut,
    dependencies=[Depends(require_admin_account)],
)
async def get_account_detail(account_id: str):
    account = await Account.get(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return AccountOut.model_validate(account, from_attributes=True)


@router.patch(
    "/accounts/{account_id}/status",
    response_model=AccountOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_account_status(account_id: str, payload: dict):
    status_value = payload.get("status")
    if not status_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="status is required"
        )
    account = await set_account_status(account_id, status_value)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return AccountOut.model_validate(account, from_attributes=True)


@router.patch(
    "/accounts/{account_id}/role",
    response_model=AccountOut,
    dependencies=[Depends(require_admin_account)],
)
async def update_account_role(account_id: str, payload: dict):
    role_id = payload.get("RoleId") or payload.get("RoleId")
    if not role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="RoleId is required"
        )
    account = await set_account_role(account_id, role_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return AccountOut.model_validate(account, from_attributes=True)
