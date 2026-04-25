"""
Team Model.

Organization unit for grouping users and boards.
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
    from app.models.board import Board


class TeamRole(str, PyEnum):
    """Team member role enumeration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Team(Base):
    """Team model for user organization."""
    
    __tablename__ = "teams"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Content
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Settings
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)
    
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
    
    # Foreign Keys
    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="teams_owned")
    members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    boards: Mapped[List["Board"]] = relationship("Board", back_populates="team")
    
    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name}, slug={self.slug})>"


class TeamMember(Base):
    """Team membership model linking users to teams."""
    
    __tablename__ = "team_members"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole),
        default=TeamRole.MEMBER,
        nullable=False,
    )
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Foreign Keys
    team_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )
    
    def __repr__(self) -> str:
        return f"<TeamMember(team={self.team_id}, user={self.user_id}, role={self.role})>"