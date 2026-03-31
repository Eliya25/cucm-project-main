import uuid
from pydantic import BaseModel, ConfigDict
from app.models.roles import UserRole




#שאני יוצר את האתר רק שם ותיאור ישלחו לי
class SiteCreate(BaseModel):
    name: str
    description: str | None = None

#מה שאני מחזיר 
class SiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)

#שיוצרים SESSION חייבים להגיד לאיזה SITE הוא שייך דרך SITE_ID
class SectionCreate(BaseModel):
    name: str
    description: str | None = None
    site_id: uuid.UUID
    classification: UserRole = UserRole.VIEWER

#מה שאני מחזרי כתגובה
class SectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    site_id: uuid.UUID
    classification: UserRole

    #כדי להמיר את האובייקט של SQLAlchemy לאובייקט של Pydantic
    model_config = ConfigDict(from_attributes=True)