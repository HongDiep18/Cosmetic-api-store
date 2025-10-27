from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Tuple
import secrets
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_passwordHash
from app.core.email import email_service
from app.modules.auth.model import Account, Role
from app.modules.users.model import User
from app.modules.auth.constants import (
    ACCOUNT_NOT_FOUND,
    EMAIL_ALREADY_USED,
    INVALID_CREDENTIALS,
    RESET_EMAIL_SENT,
    INVALID_RESET_TOKEN,
    RESET_SUCCESS,
)


async def register_user(
    Email: str,
    Password: str,
    FullName: str = "",
    Phone: str | None = None,
    Address: str | None = None,
) -> User:
    existing_account = await Account.find_one(Account.Email == Email)
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_ALREADY_USED
        )

    # Ensure default role exists (User)
    role = await Role.find_one(Role.RoleName == "User")
    if not role:
        role = Role(RoleName="User")
        await role.insert()


# ==============================
# 👤 AUTHENTICATION
# ==============================
async def authenticate_user(Email: str, Password: str) -> Tuple[Account, User]:
    """Đăng nhập người dùng bằng email + password"""
    email = Email.strip().lower()
    print(f"📧 [AUTH] Finding account with email: {email}")

    account = await Account.find_one({"Email": email})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not verify_password(Password, account.PasswordHash):
        raise HTTPException(status_code=401, detail="Invalid password")

    # 🔧 Dùng account.id (Mongo _id) chứ không phải account.AccountID
    user = await User.find_one({"AccountID": account.id})
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    print(f"✅ Authenticated user: {user.FullName}")
    return account, user


# ==============================
# 🧾 REGISTER
# ==============================
async def register_user(Email: str, Password: str, FullName: str, Phone: str, Address: str):
    """Đăng ký tài khoản mới"""
    email = Email.strip().lower()
    print(f"📩 Register new user: {email}")

    # Kiểm tra email trùng
    existing = await Account.find_one({"Email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Lấy role mặc định
    default_role = await Role.find_one({"RoleName": "User"})
    if not default_role:
        default_role = Role(RoleName="User")
        await default_role.insert()

    # 🧾 Tạo Account
    account = Account(
        Email=Email,
        PasswordHash=get_passwordHash(Password),
        RoleID=str(role.RoleID),
        Status="Active",
    )
    await account.insert()

    print(f"🧾 Account created: {account.model_dump()}")

    # 🧾 Tạo User (dùng account.id thật)
    user = User(
        AccountID=account.id,
        FullName=FullName,
        Phone=Phone,
        Address=Address,
    )
    await user.insert()

    user_dict = {
        "AccountID": str(account.id),
        "UserID": str(user.id),
        "Email": email,
        "FullName": FullName,
        "Phone": Phone,
        "Address": Address,
        "CreatedAt": user.CreatedAt,
        "UpdatedAt": user.UpdatedAt,
    }

    print(f"🧾 User dict trả về: {user_dict}")
    return user_dict


# ==============================
# 🔁 CHANGE PASSWORD
# ==============================
async def change_password(account: Account, current_password: str, new_password: str):
    """Đổi mật khẩu người dùng"""
    if not verify_password(current_password, account.PasswordHash):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    account.PasswordHash = get_passwordHash(new_password)
    await account.save()
    return {"message": "Password updated successfully"}


async def authenticate_user(email: str, password: str) -> tuple[Account, User]:
    account = await Account.find_one(Account.Email == email)
    if not account:
        return "If this email exists, a reset link has been sent."

    reset_token = secrets.token_urlsafe(32)
    account.PasswordResetToken = reset_token
    account.PasswordResetExpires = datetime.utcnow() + timedelta(hours=1)
    await account.save()

    print(f"🔗 Password reset token for {email}: {reset_token}")
    return "Password reset link sent to your email."

async def create_login_token(account: Account, role_name: str) -> str:
    return create_access_token(
        subject=str(account.AccountID), extra_claims={"role": role_name}
    )


async def change_password(
    account: Account, CurrentPassword: str, NewPassword: str
) -> None:
    if not verify_password(CurrentPassword, account.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password invalid"
        )
    account.PasswordHash = get_passwordHash(NewPassword)
    await account.save()


async def set_account_status(account_id: str, StatusValue: str) -> Account | None:
    account = await Account.get(account_id)
    if not account:
        return None
    account.Status = StatusValue
    await account.save()
    return account


async def set_account_role(account_id: str, RoleId: str) -> Account | None:
    account = await Account.get(account_id)
    if not account:
        return None
    role = await Role.get(RoleId)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    account.RoleID = RoleId
    await account.save()
    return account


async def forgot_password(Email: str) -> str:
    """
    Generate password reset token and send email.
    Always returns success message for security (prevents user enumeration).
    """
    account = await Account.find_one(Account.Email == Email)

    if account:
        # Generate secure random token
        ResetToken = secrets.token_urlsafe(32)
        hashed_token = get_passwordHash(ResetToken)

        # Set expiration time (10 minutes from now)
        ExpiresAt = datetime.utcnow() + timedelta(minutes=10)

        # Update account with reset token and expiration
        account.PasswordResetToken = hashed_token
        account.PasswordResetExpires = ExpiresAt
        await account.save()

        # Send password reset email
        await email_service.send_password_reset_email(Email, ResetToken)

    # Always return success message (security best practice)
    return RESET_EMAIL_SENT


async def reset_password(Token: str, NewPassword: str) -> str:
    """
    Reset password using the provided token.
    """
    # Hash the token to compare with stored hash
    hashed_token = get_passwordHash(Token)

    # Find account with valid token and not expired
    account = await Account.find_one(
        Account.PasswordResetToken == hashed_token,
        Account.PasswordResetExpires > datetime.utcnow(),
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_RESET_TOKEN
        )

    # Update password
    account.PasswordHash = get_passwordHash(NewPassword)

    # Clear reset token (one-time use)
    account.PasswordResetToken = None
    account.PasswordResetExpires = None

    await account.save()

    return RESET_SUCCESS
