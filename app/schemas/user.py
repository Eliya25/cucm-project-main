import uuid
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.VIEWER
    section_ids: list[uuid.UUID] = []


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    section_ids: list[uuid.UUID] = []

    @field_validator("section_ids", mode="before")
    @classmethod
    def get_ids(cls, v, info):
        if isinstance(v, list) and v and not isinstance(v[0], uuid.UUID):
            return [section.id for section in v]
        return v

    model_config = {"from_attributes": True}