"""
User Schemas.

Pydantic models for user data validation and serialization.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserInDB(UserBase):
    """Schema for user data from database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class User(UserInDB):
    """Schema for user response."""
    full_name: str = ""
    
    @classmethod
    def model_validate(cls, obj):
        instance = super().model_validate(obj)
        instance.full_name = obj.full_name if hasattr(obj, 'full_name') else ""
        return instance


class UserProfile(User):
    """Extended user profile with stats."""
    tasks_created_count: int = 0
    tasks_assigned_count: int = 0
    boards_count: int = 0
    teams_count: int = 0


class ChangePassword(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)