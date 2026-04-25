"""
Token Schemas.

Pydantic models for JWT token handling.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: Optional[UUID] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


class TokenData(BaseModel):
    """Token data extracted from JWT."""
    user_id: Optional[UUID] = None