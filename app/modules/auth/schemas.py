from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    AccessToken: str
    RefreshToken: str | None = None
    TokenType: str = "bearer"


class TokenPayload(BaseModel):
    Sub: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    fullName: str = Field(default="")
    phone: str | None = None
    address: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str = Field(min_length=6)


class RefreshTokenRequest(BaseModel):
    RefreshToken: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=6)


class RoleCreate(BaseModel):
    RoleName: str = Field(min_length=1)


class RoleOut(BaseModel):
    RoleID: str
    RoleName: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True


class AccountOut(BaseModel):
    AccountID: str
    Email: EmailStr
    RoleID: str
    Status: str
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
