import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.roles import UserRole


# ══════════════════════════════════════════
#  SITE
# ══════════════════════════════════════════
 


class SiteBase(BaseModel):
    name: str
    description: str | None = None

#שאני יוצר את האתר רק שם ותיאור ישלחו לי
class SiteCreate(SiteBase):
    group_id: uuid.UUID


class SiteUpdate(SiteBase):
    name: str | None = None
    description: str | None = None

#מה שאני מחזיר 
class SiteResponse(SiteBase):
    id: uuid.UUID
    group_id: uuid.UUID
    created_at: datetime

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════
#  SECTION
# ══════════════════════════════════════════


class SectionBase(BaseModel):
    name: str
    description: str | None = None
    classification: UserRole = UserRole.VIEWER


#שיוצרים SESSION חייבים להגיד לאיזה SITE הוא שייך דרך SITE_ID
class SectionCreate(SectionBase):
    site_id: uuid.UUID

class SectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    classification: UserRole | None = None

#מה שאני מחזרי כתגובה
class SectionResponse(SectionBase):
    id: uuid.UUID
    site_id: uuid.UUID
    created_at: datetime

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)