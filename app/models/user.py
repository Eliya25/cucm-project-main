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
    
    # Groups this user has created
    created_groups: Mapped[list["Group"]] = relationship("Group", back_populates="creator")

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    