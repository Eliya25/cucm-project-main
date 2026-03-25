import uuid
from pydantic import BaseModel


#שאני יוצר את האתר רק שם ותיאור ישלחו לי
class SiteCreate(BaseModel):
    name: str
    description: str | None = None

#מה שאני מחזיר 
class SiteResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}

#שיוצרים SESSION חייבים להגיד לאיזה SITE הוא שייך דרך SITE_ID
class SectionCreate(BaseModel):
    name: str
    site_id: uuid.UUID

#מה שאני מחזרי כתגובה
class SectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    site_id: uuid.UUID

    model_config = {"from_attributes": True}