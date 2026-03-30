import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.user import UserRole
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.device import Device

class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    sections: Mapped[list["Section"]] = relationship(
        "Section",
        secondary="section_sites",
        back_populates="sites"
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    classification: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    sites: Mapped[list["Site"]] = relationship(
        "Site",
        secondary="section_sites",
        back_populates="sections"
    )
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="section", cascade="all, delete-orphan")
