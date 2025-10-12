from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

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

    account = Account(
        Email=Email,
        PasswordHash=get_passwordHash(Password),
        RoleID=str(role.RoleID),
        Status="Active",
    )
    await account.insert()

    user = User(
        AccountID=str(account.AccountID),
        FullName=FullName,
        Phone=Phone,
        Address=Address,
    )
    await user.insert()
    return user


async def authenticate_user(email: str, password: str) -> tuple[Account, User]:
    account = await Account.find_one(Account.Email == email)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS
        )
    if not verify_password(password, account.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS
        )
    user = await User.find_one(User.AccountID == str(account.AccountID))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ACCOUNT_NOT_FOUND
        )
    return account, user


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
