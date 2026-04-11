import uuid
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID


from app.db.session import Base
from app.models.site import Section
from app.models.user import UserRole



class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    #This is the unique identifier for the device, it can be a serial number, MAC address, or any other unique string that identifies the device in the system.
    identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    #This is associated with the section that the device belongs to, it is a foreign key that references the sections table. This allows us to link each device to a specific section in the system, which can be used for organizational and access control purposes.
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)

    classification: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    section: Mapped["Section"] = relationship("Section", back_populates="devices")
    position: Mapped["DevicePosition"] = relationship("DevicePosition", back_populates="device", uselist=False)


class DevicePosition(Base):
    __tablename__ = "device_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), unique=True, nullable=False)
    x_pos: Mapped[float] = mapped_column(nullable=False)
    y_pos: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    device: Mapped["Device"] = relationship("Device", back_populates="position")

    