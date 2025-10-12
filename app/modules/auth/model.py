from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class Role(Document):
    RoleID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    RoleName: Indexed(str, unique=True)  # type: ignore[valid-type]
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roles"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)


class Account(Document):
    AccountID: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    Email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    PasswordHash: str = Field(min_length=1)
    RoleID: str
    Status: str = "Active"

    # Password reset fields
    PasswordResetToken: Optional[str] = None
    PasswordResetExpires: Optional[datetime] = None

    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "accounts"

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
