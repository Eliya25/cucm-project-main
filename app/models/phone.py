import uuid
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import List, TYPE_CHECKING

from app.db.session import Base



class PhoneMapping(Base):
    __tablename__ = "phone_mappings"

    mac_address: Mapped[str] = mapped_column(String(12), primary_key=True)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)

    section: Mapped["Section"] = relationship("Section")