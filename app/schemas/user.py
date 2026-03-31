import uuid
from pydantic import BaseModel, field_validator
from app.models.user import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER
    section_ids: list[uuid.UUID] = []


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}