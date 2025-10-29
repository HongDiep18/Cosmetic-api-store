from __future__ import annotations
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import EmailStr, Field
from bson import ObjectId


class Role(Document):
    RoleID: Optional[PydanticObjectId] = Field(
        default_factory=PydanticObjectId, alias="_id"
    )
    RoleName: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roles"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
            PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
        }

    async def save(self, *args, **kwargs):
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)


class Account(Document):
    AccountID: Optional[PydanticObjectId] = Field(
        default_factory=PydanticObjectId, alias="_id"
    )
    Email: EmailStr = Field(..., unique=True)
    PasswordHash: str
    RoleID: Optional[PydanticObjectId]
    Status: str = Field(default="Active")
    PasswordResetToken: Optional[str] = None
    PasswordResetExpires: Optional[datetime] = None
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "accounts"

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,  # Chuyển ObjectId thành string khi serialize thành JSON
            PydanticObjectId: str,  # Đảm bảo PydanticObjectId cũng được chuyển thành string
        }

    async def save(self, *args, **kwargs):  # Override phương thức save của Beanie
        self.UpdatedAt = datetime.utcnow()  # Cập nhật thời gian sửa đổi
        return await super().save(*args, **kwargs)
