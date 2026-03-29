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

    sections: Mapped[list["Section"]] = relationship("Section", back_populates="site", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)



class Section(Base):
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    classification: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    site: Mapped["Site"] = relationship("Site", back_populates="sections")
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="section", cascade="all, delete-orphan")


class SectionSite(Base):
    __tablename__ = "section_sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    section: Mapped["Section"] = relationship()
    site: Mapped["Site"] = relationship()