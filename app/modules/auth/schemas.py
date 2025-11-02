from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# =========================================
# 🪪 TOKEN SCHEMAS
# =========================================

class Token(BaseModel):
    AccessToken: str
    RefreshToken: str | None = None
    TokenType: str = "bearer"


class TokenPayload(BaseModel):
    Sub: str | None = None


# =========================================
# 👤 AUTH REQUEST SCHEMAS
# =========================================

class RegisterRequest(BaseModel):
    Email: EmailStr = Field(..., alias="Email")
    Password: str = Field(..., min_length=6, alias="Password")
    FullName: str = Field(..., alias="FullName")
    Phone: str | None = Field(default=None, alias="Phone")
    Address: str | None = Field(default=None, alias="Address")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


class LoginRequest(BaseModel):
    Email: EmailStr = Field(..., alias="Email")
    Password: str = Field(..., alias="Password")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


class ForgotPasswordRequest(BaseModel):
    Email: EmailStr = Field(..., alias="Email")


class ResetPasswordRequest(BaseModel):
    Token: str = Field(..., alias="Token")
    NewPassword: str = Field(..., min_length=6, alias="NewPassword")


class RefreshTokenRequest(BaseModel):
    RefreshToken: str = Field(..., alias="RefreshToken")


class ChangePasswordRequest(BaseModel):
    CurrentPassword: str = Field(..., alias="CurrentPassword")
    NewPassword: str = Field(..., min_length=6, alias="NewPassword")


# =========================================
# 👑 ROLE & ACCOUNT OUTPUT SCHEMAS
# =========================================

class RoleCreate(BaseModel):
    RoleName: str = Field(..., min_length=1, alias="RoleName")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


class RoleOut(BaseModel):
    RoleID: str
    RoleName: str
    CreatedAt: datetime
    UpdatedAt: datetime

    model_config = {
        "from_attributes": True,
    }


class AccountOut(BaseModel):
    AccountID: str
    Email: EmailStr
    RoleID: str
    Status: str
    CreatedAt: datetime
    UpdatedAt: datetime

    model_config = {
        "from_attributes": True,
    }

    def to_dict(self):
        # Trả về dict từ attributes
        return {
            "AccountID": self.AccountID,
            "Email": self.Email,
            "RoleID": self.RoleID,
            "Status": self.Status,
            "CreatedAt": self.CreatedAt,
            "UpdatedAt": self.UpdatedAt,
        }