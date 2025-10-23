from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid
from beanie import Document, Indexed, PydanticObjectId
from pydantic import EmailStr, Field
from bson import ObjectId
from typing import Annotated
from beanie import Indexed
from pydantic import EmailStr

class Role(Document):
    RoleID: Optional[ObjectId] = Field( alias="_id")
    RoleName: str
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roles"

    # ✅ Cho phép ObjectId và custom encoder để Pydantic không lỗi
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            PydanticObjectId: str,
        },
    }

    async def save(self, *args, **kwargs):
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)


class Account(Document):
    AccountID: Optional[PydanticObjectId] = Field(alias="_id")
    Email: Annotated[EmailStr, Indexed(unique=True)]
    PasswordHash: str
    RoleID: str
    Status: str = "Active"

    PasswordResetToken: Optional[str] = None
    PasswordResetExpires: Optional[datetime] = None

    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "accounts"

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            PydanticObjectId: str,
        },
    }

    async def save(self, *args, **kwargs):
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
