from fastapi import FastAPI  # ייבוא FastAPI כדי להגדיר את היישום
from app.db.session import engine  # מנוע SQLAlchemy מההגדרות של DB
from app.api.v1.endpoints.auth import router as auth_router  # נתיב Auth
from app.api.v1.endpoints.users import router as users_router  # נתיב Users
from app.api.v1.endpoints.sites import router as sites_router
from app.api.v1.endpoints.groups import router as groups_router  # נתיב Sites
from app.api.v1.endpoints.devices import router as devices_router  # נתיב Devices
import app.models.site
import app.models.device  # מוודא שמודלים של אתר נטענים לאלמנטים של ORM (מיגרציות ושאילתות)

app = FastAPI()  # יצירת אינסטנס של FastAPI עבור האפליקציה

# חיבור routers לנתיבי API לפי גרסה (v1)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(sites_router, prefix="/api/v1/sites", tags=["sites"])
app.include_router(groups_router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])




@app.get("/")
def read_root():
    return {"message": "welcome to cucm live"}  # נקודת קצה בסיסית שמחזירה הודעת שלום עולם   

