"""
Board Model.

Kanban-style board for organizing tasks within teams.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    func,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task
    from app.models.team import Team


class BoardRole(str, PyEnum):
    """Board member role enumeration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Board(Base):
    """Board model for task organization."""
    
    __tablename__ = "boards"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Content
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Settings
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)
    archived: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Foreign Keys
    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="boards_owned")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="boards")
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="board",
        cascade="all, delete-orphan",
    )
    members: Mapped[List["BoardMember"]] = relationship(
        "BoardMember",
        back_populates="board",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Board(id={self.id}, name={self.name})>"


class BoardMember(Base):
    """Board membership model linking users to boards with roles."""
    
    __tablename__ = "board_members"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    role: Mapped[BoardRole] = mapped_column(
        Enum(BoardRole),
        default=BoardRole.MEMBER,
        nullable=False,
    )
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Foreign Keys
    board_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="board_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_member"),
    )
    
    def __repr__(self) -> str:
        return f"<BoardMember(board={self.board_id}, user={self.user_id}, role={self.role})>"