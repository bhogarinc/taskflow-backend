"""
Task Schemas.

Pydantic models for task data validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for task creation."""
    board_id: UUID
    assignee_id: Optional[UUID] = None
    position: int = 0


class TaskUpdate(BaseModel):
    """Schema for task updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None


class TaskInDB(TaskBase):
    """Schema for task data from database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    position: int
    board_id: UUID
    created_by_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Task(TaskInDB):
    """Schema for task response with relationships."""
    assignee: Optional["UserBrief"] = None
    created_by: Optional["UserBrief"] = None


class TaskFilter(BaseModel):
    """Schema for task filtering."""
    status: Optional[List[TaskStatus]] = None
    priority: Optional[List[TaskPriority]] = None
    assignee_id: Optional[UUID] = None
    board_id: Optional[UUID] = None
    search: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None


class TaskMove(BaseModel):
    """Schema for moving task between statuses/positions."""
    status: Optional[TaskStatus] = None
    position: int
    board_id: Optional[UUID] = None


class UserBrief(BaseModel):
    """Brief user info for task relationships."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    username: str
    full_name: str = ""
    avatar_url: Optional[str] = None


# Resolve forward references
Task.model_rebuild()