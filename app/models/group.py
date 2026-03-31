import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.models.site import Site
from app.models.roles import UserRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.site import Section

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

    members: Mapped[list["User"]] = relationship("User", secondary="user_groups", back_populates="groups")

    section_groups: Mapped[list["SectionGroup"]] = relationship("SectionGroup", back_populates="group", cascade="all, delete-orphan")



class SectionGroup(Base):
    __tablename__ = "section_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
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
    user: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship()