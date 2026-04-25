"""
Team Service.

Business logic for team management operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.models.team import Team, TeamMember, TeamRole
from app.schemas.team import TeamCreate, TeamUpdate

logger = logging.getLogger(__name__)


class TeamService:
    """Service for team operations."""
    
    @staticmethod
    async def get_user_teams(
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Team]:
        """Get teams for user."""
        from sqlalchemy import or_
        
        query = select(Team).where(
            or_(
                Team.is_public == True,
                Team.owner_id == user_id,
                Team.members.any(TeamMember.user_id == user_id),
            )
        ).order_by(Team.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_team(
        db: AsyncSession,
        team_data: TeamCreate,
        user_id: UUID,
    ) -> Team:
        """Create a new team."""
        # Generate unique slug
        base_slug = slugify(team_data.name)
        slug = base_slug
        counter = 1
        
        while True:
            result = await db.execute(select(Team).where(Team.slug == slug))
            if not result.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        team = Team(
            name=team_data.name,
            slug=slug,
            description=team_data.description,
            is_public=team_data.is_public,
            owner_id=user_id,
        )
        
        db.add(team)
        await db.commit()
        await db.refresh(team)
        
        # Add owner as member
        member = TeamMember(
            team_id=team.id,
            user_id=user_id,
            role=TeamRole.OWNER,
        )
        db.add(member)
        await db.commit()
        
        logger.info(f"Team created: {team.id} ({slug}) by {user_id}")
        return team
    
    @staticmethod
    async def get_team(
        db: AsyncSession,
        team_id: UUID,
        user_id: UUID,
    ) -> Optional[Team]:
        """Get team by ID if user has access."""
        result = await db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return None
        
        has_access = (
            team.is_public or
            team.owner_id == user_id or
            any(m.user_id == user_id for m in team.members)
        )
        
        return team if has_access else None
    
    @staticmethod
    async def update_team(
        db: AsyncSession,
        team_id: UUID,
        team_data: TeamUpdate,
        user_id: UUID,
    ) -> Optional[Team]:
        """Update team."""
        result = await db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return None
        
        can_edit = (
            team.owner_id == user_id or
            any(
                m.user_id == user_id and m.role in [TeamRole.OWNER, TeamRole.ADMIN]
                for m in team.members
            )
        )
        
        if not can_edit:
            raise PermissionError("Permission denied")
        
        update_data = team_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
        
        await db.commit()
        await db.refresh(team)
        
        logger.info(f"Team updated: {team_id} by {user_id}")
        return team
    
    @staticmethod
    async def delete_team(
        db: AsyncSession,
        team_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete team."""
        result = await db.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return False
        
        if team.owner_id != user_id:
            raise PermissionError("Only owner can delete team")
        
        await db.delete(team)
        await db.commit()
        
        logger.info(f"Team deleted: {team_id} by {user_id}")
        return True