import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.roles import UserRole

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.VIEWER
    section_ids: list[uuid.UUID] = []



class UserUpdate(BaseModel):
    username: str 
    password: str 
    role: UserRole = UserRole.VIEWER
    is_active: bool | None = None
    section_ids: list[uuid.UUID] | None = None



class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}