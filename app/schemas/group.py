from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.models.roles import UserRole


class GroupBase(BaseModel):
    name: str
    description: str | None = None
    classification: UserRole = UserRole.VIEWER


class GroupCreate(GroupBase):
    pass

class GroupResponse(GroupBase):
    id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)


class UserGroupCreate(BaseModel):
    user_id: uuid.UUID
    group_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)