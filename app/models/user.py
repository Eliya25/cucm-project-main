import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.group import Group
from app.models.roles import UserRole

from app.db.session import Base



class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Groups this user has created
    created_groups: Mapped[list["Group"]] = relationship("Group", back_populates="creator")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    groups: Mapped[list["Group"]] = relationship("Group", secondary="user_groups", back_populates="members")

    @property
    def allowed_sections(self) -> list:

        # This property calculates the sections that the user has access to based on the groups they belong to. It iterates through each group the user is a member of, 
        # and for each group, it collects the sections associated with that group through the section_groups relationship. 
        # Finally, it returns a unique list of sections that the user has access to.

        sections = []

        for group in self.groups:
            for section_group in group.section_groups:
                sections.append(section_group.section)
        
        return list(set(sections))
    
    def is_admin_of_section(self, section_id: uuid.UUID) -> bool:
        # This method checks if the user has admin privileges for a specific section. It iterates through the groups the user belongs to and checks if any of those groups have admin rights for the given section ID. 
        # If it finds a match, it returns True, indicating that the user is an admin of that section; otherwise, it returns False.

        if self.role == UserRole.SUPERADMIN:
            return True

        for group in self.groups:
            for section_group in group.section_groups:
                if section_group.section_id == section_id and section_group.is_admin:
                    return True
        
        return False