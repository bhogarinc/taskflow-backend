"""
User Routes.

User profile management and search.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import User, UserUpdate, UserProfile
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.auth_service import AuthService
from app.api.deps import get_current_active_user, get_current_superuser

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile with stats."""
    # TODO: Add stats aggregation
    return UserProfile.model_validate(current_user)


@router.patch("/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    updated_user = await AuthService.update_user(
        db, current_user.id, user_data
    )
    return updated_user


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get user by ID."""
    user = await AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/", response_model=PaginatedResponse[User])
async def list_users(
    search: str = Query(None, description="Search by username or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser),
):
    """List all users (superuser only)."""
    from sqlalchemy import select, func, or_
    from app.models.user import User
    
    # Build query
    query = select(User)
    count_query = select(func.count(User.id))
    
    if search:
        filter_condition = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        )
        query = query.where(filter_condition)
        count_query = count_query.where(filter_condition)
    
    # Pagination
    params = PaginationParams(page=page, page_size=page_size)
    query = query.offset(params.offset).limit(params.page_size)
    
    # Execute
    result = await db.execute(query)
    users = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return PaginatedResponse.create(list(users), total, params)