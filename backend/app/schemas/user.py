import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.roles import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER



class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str