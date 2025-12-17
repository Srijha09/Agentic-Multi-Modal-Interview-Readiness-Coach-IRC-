"""User schemas."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

