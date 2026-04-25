"""
Authentication Service.

Business logic for user authentication and management.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate user by email and password."""
        result = await db.execute(
            select(User).where(
                (User.email == email) & (User.is_active == True)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserCreate,
    ) -> Tuple[User, Token]:
        """Register a new user."""
        # Check for existing email
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Check for existing username
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("Username already taken")
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            bio=user_data.bio,
            hashed_password=get_password_hash(user_data.password),
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Generate tokens
        token = AuthService.create_token_pair(str(user.id))
        
        logger.info(f"User registered: {user.email}")
        return user, token
    
    @staticmethod
    def create_token_pair(user_id: str) -> Token:
        """Create access and refresh token pair."""
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes in seconds
        )
    
    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> Optional[Token]:
        """Refresh access token using refresh token."""
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            return None
        
        # Verify user still exists and is active
        result = await db.execute(
            select(User).where(
                (User.id == user_id) & (User.is_active == True)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return AuthService.create_token_pair(str(user.id))
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        return True
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: UUID,
        user_data: UserUpdate,
    ) -> Optional[User]:
        """Update user profile."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return user