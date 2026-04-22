import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base
from app.models.roles import UserRole

if TYPE_CHECKING:
    from app.models.group import UserGroup, Group


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    created_groups: Mapped[list["Group"]] = relationship("Group", back_populates="creator")

    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="user_groups", back_populates="members",
        overlaps="user, group"
    )

    user_groups_links: Mapped[list["UserGroup"]] = relationship(
        "UserGroup", back_populates="user", overlaps="groups, members"
    )

    @property
    def allowed_sections(self) -> list:
        sections = []
        seen_ids = set()
        for link in self.user_groups_links:
            if link.group is None:
                continue
            for sg in link.group.section_groups:
                if sg.section_id not in seen_ids:
                    seen_ids.add(sg.section_id)
                    sections.append(sg.section)
        return sections

    @property
    def allowed_section_ids(self) -> set[uuid.UUID]:
       
        return {s.id for s in self.allowed_sections}

    def is_admin_of_section(self, section_id: uuid.UUID) -> bool:
        if self.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            return True
        for link in self.user_groups_links:
            if link.group is None:
                continue
            for sg in link.group.section_groups:
                if sg.section_id == section_id and sg.is_admin:
                    return True
        return False

    def has_section_access(self, section_id: uuid.UUID) -> bool:
        if self.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            return True
        return section_id in self.allowed_section_ids 