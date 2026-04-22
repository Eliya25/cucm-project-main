import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, func, Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.models.roles import UserRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.site import Section, Site

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    #who created the group
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    classification: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    creator: Mapped["User"] = relationship("User", back_populates="created_groups", foreign_keys=[creator_id])

    members: Mapped[list["User"]] = relationship("User", secondary="user_groups", back_populates="groups", overlaps="user_groups_links")

    section_groups: Mapped[list["SectionGroup"]] = relationship("SectionGroup", back_populates="group", cascade="all, delete-orphan")
    sites: Mapped[list["Site"]] = relationship("Site", back_populates="group", cascade="all, delete-orphan")
    user_groups_links: Mapped[list["UserGroup"]] = relationship("UserGroup", back_populates="group", overlaps="groups,members")



class SectionGroup(Base):
    __tablename__ = "section_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    section: Mapped["Section"] = relationship()
    group: Mapped["Group"] = relationship("Group", back_populates="section_groups")

class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # מי המשתמשים בקבוצה
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # באיזו קבוצה הוא נמצא
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # קשר לטבלאות המשתמשים והקבוצות
    user: Mapped["User"] = relationship(back_populates="user_groups_links", overlaps="groups, members")
    group: Mapped["Group"] = relationship(back_populates="user_groups_links", overlaps="groups, members")