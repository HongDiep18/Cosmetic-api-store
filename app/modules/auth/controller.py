from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
import secrets

from app.core.config import settings
from app.modules.auth.model import Account, Profile
from app.core.security import get_passwordHash

# ==============================
# 🔐 Cấu hình mật khẩu & JWT
# ==============================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 ngày
ALGORITHM = "HS256"


# ==============================
# 🔒 Utilities
# ==============================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu người dùng"""
    return pwd_context.verify(plain_password, hashed_password)


def create_login_token(account: Account) -> str:
    """Tạo access token JWT"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Use account.id instead of account._id (Beanie uses .id property)
    account_id = str(account.id)
    payload = {
        "sub": account_id,
        "role": account.role,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token


# ==============================
# 👤 AUTHENTICATION
# ==============================
async def authenticate_user(Email: str, Password: str) -> Account:
    """Đăng nhập người dùng bằng email + password"""
    email = Email.strip().lower()
    print(f"📧 [AUTH] Finding account with email: {email}")

    account = await Account.find_one({"email": email})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not verify_password(Password, account.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid password")

    print(f"✅ Authenticated user: {account.profile.fullName} (Role: {account.role})")
    return account


# ==============================
# 🧾 REGISTER
# ==============================
async def register_user(
    Email: str, Password: str, FullName: str, Phone: str, Address: str
):
    """Đăng ký tài khoản mới"""
    email = Email.strip().lower()
    print(f"📩 Register new user: {email}")

    # Kiểm tra email trùng
    existing = await Account.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🧾 Tạo Account với profile nhúng
    profile = Profile(
        fullName=FullName,
        phone=Phone,
        address=Address,
    )

    account = Account(
        email=email,
        passwordHash=get_passwordHash(Password),
        role="User",
        status="Active",
        profile=profile,
    )
    await account.insert()

    print(f"🧾 Account created: {account.model_dump()}")

    account_dict = {
        "_id": str(account.id),
        "email": email,
        "role": "User",
        "status": "Active",
        "profile": {
            "fullName": FullName,
            "phone": Phone,
            "address": Address,
        },
        "createdAt": account.createdAt,
        "updatedAt": account.updatedAt,
    }

    print(f"🧾 Account dict trả về: {account_dict}")
    return account_dict


# ==============================
# 🔁 CHANGE PASSWORD
# ==============================
async def change_password(account: Account, current_password: str, new_password: str):
    """Đổi mật khẩu người dùng"""
    if not verify_password(current_password, account.passwordHash):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    account.passwordHash = get_passwordHash(new_password)
    await account.save()
    return {"message": "Password updated successfully"}


# ==============================
# 🔑 FORGOT PASSWORD
# ==============================
async def forgot_password(email: str):
    """Yêu cầu đặt lại mật khẩu"""
    email = email.strip().lower()
    account = await Account.find_one({"email": email})
    if not account:
        return "If this email exists, a reset link has been sent."

    reset_token = secrets.token_urlsafe(32)
    account.passwordResetToken = reset_token
    account.passwordResetExpires = datetime.utcnow() + timedelta(hours=1)
    await account.save()

    print(f"🔗 Password reset token for {email}: {reset_token}")
    return "Password reset link sent to your email."


# ==============================
# 🔁 RESET PASSWORD
# ==============================
async def reset_password(token: str, new_password: str):
    """Đặt lại mật khẩu bằng token"""
    account = await Account.find_one({"passwordResetToken": token})
    if (
        not account
        or not account.passwordResetExpires
        or account.passwordResetExpires < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    account.passwordHash = get_passwordHash(new_password)
    account.passwordResetToken = None
    account.passwordResetExpires = None
    await account.save()
    return "Password reset successful."


# ==============================
# ⚙️ ADMIN - CẬP NHẬT ROLE / STATUS
# ==============================
async def set_account_status(account_id: str, status_value: str):
    account = await Account.get(account_id)
    if not account:
        return None
    account.status = status_value
    await account.save()
    return account


async def set_account_role(account_id: str, role_name: str):
    account = await Account.get(account_id)
    if not account:
        return None
    account.role = role_name
    await account.save()
    return account
