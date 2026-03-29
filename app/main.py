from fastapi import FastAPI  # ייבוא FastAPI כדי להגדיר את היישום
from sqlalchemy import text  # ייבוא כדי להריץ שאילתא פשוטה ל-check db

from app.db.session import engine  # מנוע SQLAlchemy מההגדרות של DB
from app.api.v1.endpoints.auth import router as auth_router  # נתיב Auth
from app.api.v1.endpoints.users import router as users_router  # נתיב Users
from app.api.v1.endpoints.sites import router as sites_router
from app.api.v1.endpoints.phones import router as phones_router  # נתיב Sites
import app.models.site
import app.models.device  # מוודא שמודלים של אתר נטענים לאלמנטים של ORM (מיגרציות ושאילתות)

app = FastAPI()  # יצירת אינסטנס של FastAPI עבור האפליקציה

# חיבור routers לנתיבי API לפי גרסה (v1)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(sites_router, prefix="/api/v1/sites", tags=["sites"])
app.include_router(phones_router, prefix="/api/v1/phones", tags=["phones"])




@app.get("/")
def read_root():
    return {"message": "welcome to cucm live"}  # נקודת קצה בסיסית שמחזירה הודעת שלום עולם   

@app.get("/health")  # נקודת בדיקת חיים בסיסית
def haelth_check():
    return {"status": "ok"}  # החזר מצב תקין


@app.get("/health/db")  # נקודת בדיקת חיבור למסד נתונים
def get_health():
    try:
        with engine.connect() as conn:  # פתיחת חיבור זמני ל-DB
            conn.execute(text("SELECT 1"))  # ביצוע שאילתא פשוטה לשם בדיקה
        return {"status": "ok", "database": "connected"}  # DB ענה
    except Exception as e:
        return {"status": "error", "database": str(e)}  # במקרה של שגיאה, נוחת סטטוס שגיאה