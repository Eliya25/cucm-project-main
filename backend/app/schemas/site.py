import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.roles import UserRole




class SiteBase(BaseModel):
    name: str
    description: str | None = None

#שאני יוצר את האתר רק שם ותיאור ישלחו לי
class SiteCreate(SiteBase):
    group_id: uuid.UUID

#מה שאני מחזיר 
class SiteResponse(SiteBase):
    id: uuid.UUID
    group_id: uuid.UUID
    created_at: datetime

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[uuid.UUID] = None

class SectionBase(BaseModel):
    name: str
    description: str | None = None
    classification: UserRole = UserRole.VIEWER


#שיוצרים SESSION חייבים להגיד לאיזה SITE הוא שייך דרך SITE_ID
class SectionCreate(SectionBase):
    site_id: uuid.UUID

#מה שאני מחזרי כתגובה
class SectionResponse(SectionBase):
    id: uuid.UUID
    site_id: uuid.UUID
    created_at: datetime

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)