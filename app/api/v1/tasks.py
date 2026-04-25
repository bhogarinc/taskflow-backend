"""
Task Routes.

Task CRUD operations and board management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import TaskStatus, TaskPriority
from app.schemas.task import (
    Task, TaskCreate, TaskUpdate, TaskFilter, TaskMove,
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.task_service import TaskService
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Task])
async def list_tasks(
    board_id: Optional[UUID] = Query(None),
    status: Optional[List[TaskStatus]] = Query(None),
    priority: Optional[List[TaskPriority]] = Query(None),
    assignee_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List tasks with filtering."""
    filter_params = TaskFilter(
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
    )
    
    if board_id:
        tasks = await TaskService.get_board_tasks(
            db, board_id, current_user.id, filter_params
        )
        total = len(tasks)
        # Manual pagination for filtered list
        params = PaginationParams(page=page, page_size=page_size)
        start = params.offset
        end = start + params.page_size
        paginated_tasks = tasks[start:end]
    else:
        tasks = await TaskService.get_user_tasks(db, current_user.id, filter_params)
        total = len(tasks)
        params = PaginationParams(page=page, page_size=page_size)
        start = params.offset
        end = start + params.page_size
        paginated_tasks = tasks[start:end]
    
    return PaginatedResponse.create(paginated_tasks, total, params)


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Create a new task."""
    try:
        task = await TaskService.create_task(db, task_data, current_user.id)
        return task
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get task by ID."""
    task = await TaskService._get_task_with_access(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )
    return task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Update a task."""
    task = await TaskService.update_task(db, task_id, task_data, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )
    return task


@router.post("/{task_id}/move", response_model=Task)
async def move_task(
    task_id: UUID,
    move_data: TaskMove,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Move task to different status/position."""
    task = await TaskService.move_task(db, task_id, move_data, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Delete a task."""
    success = await TaskService.delete_task(db, task_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied",
        )
    return None