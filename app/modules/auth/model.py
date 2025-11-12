from __future__ import annotations
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import EmailStr, Field, BaseModel
from bson import ObjectId


# Profile schema for embedded document
class Profile(BaseModel):
    fullName: str
    phone: str
    address: Optional[str] = None  # Only for User role


# Unified Account model - gộp accounts, users, shippers, roles thành 1
class Account(Document):
    email: EmailStr = Field(..., unique=True)
    passwordHash: str
    role: str  # "User", "Admin", "Shipper"
    status: str = Field(default="Active")
    profile: Profile
    passwordResetToken: Optional[str] = None
    passwordResetExpires: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "accounts"

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            PydanticObjectId: str,
        }

    async def save(self, *args, **kwargs):
        self.updatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)

    # Property aliases for backward compatibility (optional)
    @property
    def AccountID(self):
        return self.id

    @property
    def Email(self):
        return self.email

    @property
    def PasswordHash(self):
        return self.passwordHash

    @property
    def Role(self):
        return self.role

    @property
    def Status(self):
        return self.status

    @property
    def PasswordResetToken(self):
        return self.passwordResetToken

    @property
    def PasswordResetExpires(self):
        return self.passwordResetExpires

    @property
    def CreatedAt(self):
        return self.createdAt

    @property
    def UpdatedAt(self):
        return self.updatedAt
