from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from beanie import PydanticObjectId
from app.core.config import settings
from app.modules.auth.model import Account, Role


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_account(token: str = Depends(oauth2_scheme)) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        account_id: Optional[str] = payload.get("sub")
        if account_id is None:
            raise credentials_exception
        
        
        account = await Account.get(PydanticObjectId(account_id))

        if not account:
            raise credentials_exception

        return account

    except (JWTError, Exception) as e:
        print("❌ Token decode/get_current_account error:", e)
        raise credentials_exception


async def require_admin_account(
    current_account: Account = Depends(get_current_account),
) -> Account:
    role = await Role.get(current_account.RoleID)
    if not role or role.RoleName.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privilege required"
        )
    return current_account
