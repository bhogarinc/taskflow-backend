"""
User Model.

Core user entity with authentication and profile data.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.board import Board, BoardMember
    from app.models.team import Team, TeamMember


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Profile
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    tasks_created: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.created_by_id",
        back_populates="created_by",
    )
    tasks_assigned: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        back_populates="assignee",
    )
    boards_owned: Mapped[List["Board"]] = relationship(
        "Board",
        back_populates="owner",
    )
    board_memberships: Mapped[List["BoardMember"]] = relationship(
        "BoardMember",
        back_populates="user",
    )
    teams_owned: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="owner",
    )
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
    )
    
    @property
    def full_name(self) -> str:
        """Return full name or username."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"