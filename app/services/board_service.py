"""
Board Service.

Business logic for board management operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import Board, BoardMember, BoardRole
from app.models.team import TeamMember, TeamRole
from app.schemas.board import BoardCreate, BoardUpdate

logger = logging.getLogger(__name__)


class BoardService:
    """Service for board operations."""
    
    @staticmethod
    async def get_user_boards(
        db: AsyncSession,
        user_id: UUID,
        include_archived: bool = False,
    ) -> List[Board]:
        """Get boards accessible to user."""
        from sqlalchemy import or_
        
        query = select(Board).where(
            or_(
                Board.is_public == True,
                Board.owner_id == user_id,
                Board.members.any(BoardMember.user_id == user_id),
            )
        )
        
        if not include_archived:
            query = query.where(Board.archived == False)
        
        query = query.order_by(Board.updated_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_board(
        db: AsyncSession,
        board_data: BoardCreate,
        user_id: UUID,
    ) -> Board:
        """Create a new board."""
        # Verify team membership if team specified
        if board_data.team_id:
            result = await db.execute(
                select(TeamMember).where(
                    and_(
                        TeamMember.team_id == board_data.team_id,
                        TeamMember.user_id == user_id,
                    )
                )
            )
            if not result.scalar_one_or_none():
                raise PermissionError("Not a member of this team")
        
        board = Board(
            name=board_data.name,
            description=board_data.description,
            is_public=board_data.is_public,
            owner_id=user_id,
            team_id=board_data.team_id,
        )
        
        db.add(board)
        await db.commit()
        await db.refresh(board)
        
        # Add owner as member
        member = BoardMember(
            board_id=board.id,
            user_id=user_id,
            role=BoardRole.OWNER,
        )
        db.add(member)
        await db.commit()
        
        logger.info(f"Board created: {board.id} by {user_id}")
        return board
    
    @staticmethod
    async def get_board(
        db: AsyncSession,
        board_id: UUID,
        user_id: UUID,
    ) -> Optional[Board]:
        """Get board by ID if user has access."""
        result = await db.execute(
            select(Board).where(Board.id == board_id)
        )
        board = result.scalar_one_or_none()
        
        if not board:
            return None
        
        has_access = (
            board.is_public or
            board.owner_id == user_id or
            any(m.user_id == user_id for m in board.members)
        )
        
        return board if has_access else None
    
    @staticmethod
    async def update_board(
        db: AsyncSession,
        board_id: UUID,
        board_data: BoardUpdate,
        user_id: UUID,
    ) -> Optional[Board]:
        """Update board."""
        result = await db.execute(
            select(Board).where(Board.id == board_id)
        )
        board = result.scalar_one_or_none()
        
        if not board:
            return None
        
        # Check edit permission
        can_edit = (
            board.owner_id == user_id or
            any(
                m.user_id == user_id and m.role in [BoardRole.OWNER, BoardRole.ADMIN]
                for m in board.members
            )
        )
        
        if not can_edit:
            raise PermissionError("Permission denied")
        
        update_data = board_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(board, field, value)
        
        await db.commit()
        await db.refresh(board)
        
        logger.info(f"Board updated: {board_id} by {user_id}")
        return board
    
    @staticmethod
    async def delete_board(
        db: AsyncSession,
        board_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete board."""
        result = await db.execute(
            select(Board).where(Board.id == board_id)
        )
        board = result.scalar_one_or_none()
        
        if not board:
            return False
        
        if board.owner_id != user_id:
            raise PermissionError("Only owner can delete board")
        
        await db.delete(board)
        await db.commit()
        
        logger.info(f"Board deleted: {board_id} by {user_id}")
        return True