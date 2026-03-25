import uuid
from enum import Enum
from typing import List, TYPE_CHECKING # הוספנו TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy

from app.db.session import Base

# פתרון לשגיאת ה-Undefined:
# אנחנו מייבאים את Section רק לצורך "בדיקת סוגים" של ה-IDE, 
# אבל בזמן ריצה פייתון יתעלם מהשורה הזו ולא ייווצר Import מעגלי.
if TYPE_CHECKING:
    from app.models.site import Section

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class UserSection(Base):
    __tablename__ = "user_sections"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), primary_key=True)

    # משתמשים במחרוזת "User" ו-"Section" במקום ב-Class עצמו
    user: Mapped["User"] = relationship(back_populates="section_associations")
    section: Mapped["Section"] = relationship()

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)

    # קשר לטבלת המתווך
    section_associations: Mapped[List["UserSection"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )

    # הפרוקסי - שים לב שגם פה ב-Type Hint אנחנו משתמשים ב-"Section" בתוך גרשיים
    allowed_sections: AssociationProxy[List["Section"]] = association_proxy("section_associations", "section")

    @property
    def section_ids(self) -> list[uuid.UUID]:
        # מאפשר לקבל IDs של הסקשנים שבהם המשתמש מקושר
        return [section.id for section in self.allowed_sections]