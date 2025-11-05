from datetime import datetime, timedelta
from typing import Tuple
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
import secrets

from app.core.config import settings
from app.modules.auth.model import Account, Role
from app.modules.users.model import User

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


def get_password_hash(password: str) -> str:
    """Hash mật khẩu trước khi lưu"""
    return pwd_context.hash(password)


def create_login_token(account: Account, role_name: str) -> str:
    """Tạo access token JWT"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(account.id),
        "role": role_name,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token


# ==============================
# 👤 AUTHENTICATION
# ==============================
async def authenticate_user(Email: str, Password: str) -> Tuple[Account, User]:
    """Đăng nhập người dùng bằng email + password"""
    email = Email.strip().lower()
    print(f"📧 [AUTH] Finding account with email: {email}")

    account = await Account.find_one({"Email": email})
    if not account:
        print(f"❌ [AUTH] Account not found for email: {email}")
        raise HTTPException(status_code=404, detail="Account not found")

    print(f"✅ [AUTH] Account found: {account.id}")
    print(f"🔐 [AUTH] Verifying password...")
    
    is_valid = verify_password(Password, account.PasswordHash)
    print(f"🔐 [AUTH] Password verification result: {is_valid}")
    print(f"🔐 [AUTH] PasswordHash length: {len(account.PasswordHash) if account.PasswordHash else 0}")
    
    if not is_valid:
        print(f"❌ [AUTH] Invalid password for email: {email}")
        raise HTTPException(status_code=401, detail="Invalid password")

    # 🔧 Dùng account.id (Mongo _id) chứ không phải account.AccountID
    user = await User.find_one({"AccountID": account.id})
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    print(f" Authenticated user: {user.FullName}")
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
        Email=email,
        PasswordHash=get_password_hash(Password),
        RoleID=str(default_role.id),
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

    account.PasswordHash = get_password_hash(new_password)
    await account.save()
    return {"message": "Password updated successfully"}


# ==============================
# 🔑 FORGOT PASSWORD
# ==============================
async def forgot_password(email: str):
    """Yêu cầu đặt lại mật khẩu"""
    email = email.strip().lower()
    account = await Account.find_one({"Email": email})
    if not account:
        return "If this email exists, a reset link has been sent."

    reset_token = secrets.token_urlsafe(32)
    account.PasswordResetToken = reset_token
    account.PasswordResetExpires = datetime.utcnow() + timedelta(hours=1)
    await account.save()

    print(f"🔗 Password reset token for {email}: {reset_token}")
    return "Password reset link sent to your email."


# ==============================
# 🔁 RESET PASSWORD
# ==============================
async def reset_password(token: str, new_password: str):
    """Đặt lại mật khẩu bằng token"""
    account = await Account.find_one({"PasswordResetToken": token})
    if (
        not account
        or not account.PasswordResetExpires
        or account.PasswordResetExpires < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    account.PasswordHash = get_password_hash(new_password)
    account.PasswordResetToken = None
    account.PasswordResetExpires = None
    await account.save()
    return "Password reset successful."


# ==============================
# ⚙️ ADMIN - CẬP NHẬT ROLE / STATUS
# ==============================
async def set_account_status(account_id: str, status_value: str):
    account = await Account.get(account_id)
    if not account:
        return None
    account.Status = status_value
    await account.save()
    return account


async def set_account_role(account_id: str, role_id: str):
    account = await Account.get(account_id)
    if not account:
        return None
    account.RoleID = role_id
    await account.save()
    return account
