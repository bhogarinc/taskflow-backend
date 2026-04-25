"""
Task Service.

Business logic for task management operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.board import Board, BoardMember, BoardRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskMove

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task operations."""
    
    @staticmethod
    async def get_board_tasks(
        db: AsyncSession,
        board_id: UUID,
        user_id: UUID,
        filter_params: Optional[TaskFilter] = None,
    ) -> List[Task]:
        """Get tasks for a board with optional filtering."""
        # Check access
        has_access = await TaskService._check_board_access(db, board_id, user_id)
        if not has_access:
            return []
        
        query = select(Task).where(Task.board_id == board_id)
        
        # Apply filters
        if filter_params:
            if filter_params.status:
                query = query.where(Task.status.in_(filter_params.status))
            if filter_params.priority:
                query = query.where(Task.priority.in_(filter_params.priority))
            if filter_params.assignee_id:
                query = query.where(Task.assignee_id == filter_params.assignee_id)
            if filter_params.search:
                search_term = f"%{filter_params.search}%"
                query = query.where(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term),
                    )
                )
            if filter_params.due_before:
                query = query.where(Task.due_date <= filter_params.due_before)
            if filter_params.due_after:
                query = query.where(Task.due_date >= filter_params.due_after)
        
        # Order by position for board view
        query = query.order_by(Task.status, Task.position)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_task(
        db: AsyncSession,
        task_data: TaskCreate,
        user_id: UUID,
    ) -> Task:
        """Create a new task."""
        # Check board access
        can_edit = await TaskService._check_board_edit_access(
            db, task_data.board_id, user_id
        )
        if not can_edit:
            raise PermissionError("No permission to create tasks in this board")
        
        # Set started_at if status is in_progress
        started_at = None
        if task_data.status == TaskStatus.IN_PROGRESS:
            started_at = datetime.utcnow()
        
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            position=task_data.position,
            board_id=task_data.board_id,
            assignee_id=task_data.assignee_id,
            created_by_id=user_id,
            started_at=started_at,
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task created: {task.id} by {user_id}")
        return task
    
    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: UUID,
        task_data: TaskUpdate,
        user_id: UUID,
    ) -> Optional[Task]:
        """Update a task."""
        task = await TaskService._get_task_with_access(db, task_id, user_id)
        if not task:
            return None
        
        # Track status changes for timestamps
        old_status = task.status
        
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        # Update timestamps based on status
        new_status = update_data.get("status")
        if new_status and new_status != old_status:
            if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.utcnow()
            elif new_status == TaskStatus.DONE and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif old_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
                task.completed_at = None
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(f"Task updated: {task_id} by {user_id}")
        return task
    
    @staticmethod
    async def move_task(
        db: AsyncSession,
        task_id: UUID,
        move_data: TaskMove,
        user_id: UUID,
    ) -> Optional[Task]:
        """Move task to different status/position."""
        task = await TaskService._get_task_with_access(db, task_id, user_id)
        if not task:
            return None
        
        old_status = task.status
        
        if move_data.status:
            task.status = move_data.status
            if move_data.status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.utcnow()
            elif move_data.status == TaskStatus.DONE and not task.completed_at:
                task.completed_at = datetime.utcnow()
        
        task.position = move_data.position
        
        await db.commit()
        await db.refresh(task)
        
        logger.info(
            f"Task moved: {task_id} from {old_status} to {task.status} "
            f"position {task.position} by {user_id}"
        )
        return task
    
    @staticmethod
    async def delete_task(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a task."""
        task = await TaskService._get_task_with_edit_access(db, task_id, user_id)
        if not task:
            return False
        
        await db.delete(task)
        await db.commit()
        
        logger.info(f"Task deleted: {task_id} by {user_id}")
        return True
    
    @staticmethod
    async def get_user_tasks(
        db: AsyncSession,
        user_id: UUID,
        filter_params: Optional[TaskFilter] = None,
    ) -> List[Task]:
        """Get tasks assigned to or created by user."""
        query = select(Task).where(
            or_(
                Task.assignee_id == user_id,
                Task.created_by_id == user_id,
            )
        )
        
        if filter_params:
            if filter_params.status:
                query = query.where(Task.status.in_(filter_params.status))
            if filter_params.priority:
                query = query.where(Task.priority.in_(filter_params.priority))
        
        query = query.order_by(Task.due_date, Task.priority)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def _check_board_access(
        db: AsyncSession,
        board_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if user has access to board."""
        result = await db.execute(
            select(Board).where(
                (Board.id == board_id) &
                (
                    (Board.is_public == True) |
                    (Board.owner_id == user_id) |
                    Board.members.any(BoardMember.user_id == user_id)
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def _check_board_edit_access(
        db: AsyncSession,
        board_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Check if user can edit tasks in board."""
        result = await db.execute(
            select(Board).where(
                (Board.id == board_id) &
                (
                    (Board.owner_id == user_id) |
                    Board.members.any(
                        and_(
                            BoardMember.user_id == user_id,
                            BoardMember.role.in_([
                                BoardRole.OWNER,
                                BoardRole.ADMIN,
                                BoardRole.MEMBER,
                            ])
                        )
                    )
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def _get_task_with_access(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> Optional[Task]:
        """Get task if user has access."""
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        has_access = await TaskService._check_board_access(
            db, task.board_id, user_id
        )
        return task if has_access else None
    
    @staticmethod
    async def _get_task_with_edit_access(
        db: AsyncSession,
        task_id: UUID,
        user_id: UUID,
    ) -> Optional[Task]:
        """Get task if user has edit access."""
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        has_access = await TaskService._check_board_edit_access(
            db, task.board_id, user_id
        )
        return task if has_access else None