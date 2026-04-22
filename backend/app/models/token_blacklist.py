import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class TokenBlacklist(Base):
    # This model represents a blacklist of JWT tokens that have been revoked. It contains the unique identifier (jti) of the token and the timestamp of when it was blacklisted. This allows the system to check if a token has been revoked and prevent its use for authentication or authorization.
    __tablename__ = "token_blacklist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)  # JWT ID
    revoked_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # When the token would naturally expire