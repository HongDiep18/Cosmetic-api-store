from __future__ import annotations
from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field, field_validator, ConfigDict
from bson import ObjectId


class Product(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    ProductName: Indexed(str)  # type: ignore[valid-type]
    Description: str
    Price: float = Field(ge=0)
    Stock: int = Field(ge=0)
    Status: str = "Active"
    Image: Optional[str] = None
    CategoryID: str  # Lưu ObjectId của Category dưới dạng string
    CategoryName: Optional[str] = None  # Added for filtering
    
    @field_validator("CategoryID", mode="before")
    @classmethod
    def convert_category_id(cls, v):
        # Chuyển đổi ObjectId sang string
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, PydanticObjectId):
            return str(v)
        return v
    Brand: Optional[str] = None  # Added for filtering and display
    Rating: Optional[float] = Field(default=0.0, ge=0, le=5)  # Product rating
    ReviewCount: Optional[int] = Field(default=0, ge=0)  # Number of reviews
    IsFeatured: Optional[bool] = False  # Featured product flag
    IsNew: Optional[bool] = False  # New product flag
    OriginalPrice: Optional[float] = None  # Original price for discount display
    CreatedAt: datetime = Field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = Field(default_factory=datetime.utcnow)

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure _id is always converted to string in the output
        if hasattr(self, "_id"):
            self._id = str(self._id)

    class Settings:
        name = "products"
        use_revision = False  # Tắt revision để không có revision_id trong document

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            PydanticObjectId: str,
        },
    )

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.UpdatedAt = datetime.utcnow()
        return await super().save(*args, **kwargs)
