import sys
import os
import time

from fastapi import FastAPI, Request  # ייבוא FastAPI כדי להגדיר את היישום
from fastapi.middleware.cors import CORSMiddleware  # ייבוא CORS Middleware לניהול מדיניות CORS
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal  # בסיס המודלים של SQLAlchemy
from app.api.v1.endpoints.auth import router as auth_router  # נתיב Auth
from app.api.v1.endpoints.users import router as users_router  # נתיב Users
from app.api.v1.endpoints.sites import router as sites_router
from app.api.v1.endpoints.groups import router as groups_router  # נתיב Sites
from app.api.v1.endpoints.devices import router as devices_router  # נתיב Devices

import app.models.user  # מוודא שמודלים של משתמש נטענים לאלמנטים של ORM (מיגרציות ושאילתות)
import app.models.site
import app.models.device  # מוודא שמודלים של אתר נטענים לאלמנטים של ORM (מיגרציות ושאילתות)
import app.models.group  # מוודא שמודלים של קבוצה נטענים לאלמנטים של ORM (מיגרציות ושאילתות)
import app.models.token_blacklist


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_manager import LoggerManager
from app.core.jwt import decode_access_token
from app.models.user import User

Base.metadata.create_all(bind=engine)  # יצירת טבלאות במסד הנתונים לפי המודלים שהוגדרו ב-SQLAlchemy


app = FastAPI(title="CUCM Portal API", description="Phone managment system for cucm")  # יצירת אינסטנס של FastAPI עבור האפליקציה


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # מאפשר גישה מכל המקורות (ניתן להגביל לפי צורך)
    allow_credentials=True,  # מאפשר שליחת עוגיות ואישורים  
    allow_methods=["*"],  # מאפשר את כל שיטות ה-HTTP
    allow_headers=["*"],  # מאפשר את כל הכותרות
)  # הוספת Middleware לניהול CORS כדי לאפשר גישה בין דומיינים שונים   


@app.on_event("startup")
async def startup_event():

    LoggerManager.initialize(path_prefix="logs")
    LoggerManager.get_logger().info("-- CUCM Portal satarted --")


def _get_user_info_from_request(request: Request) -> str:
    
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
 
    if not token:
        return "Anonymous"
 
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return "Anonymous"
 
        # שליפת שם ורמת המשתמש מה-DB
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return f"{user.username} [{user.role.value}]"
            return f"ID:{user_id} [unknown]"
        finally:
            db.close()
 
    except JWTError:
        return "Anonymous [invalid token]"
    except Exception:
        return "Anonymous [error]"
 


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    logger = LoggerManager.get_logger()
    start_time = time.time()

    method = request.method
    path = request.url.path
    client_ip = request.client.host

    # Try to extract user from Authorization header
    user_info = _get_user_info_from_request(request)

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000 , 2)

    log_msg = f"[{method}] {path} | Status: {response.status_code} | Time: {process_time}ms | IP: {client_ip} | User: {user_info}"

    if response.status_code >= 400:
        logger.error(log_msg)
    else:
        logger.info(log_msg)
    
    return response
        


# חיבור routers לנתיבי API לפי גרסה (v1)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(sites_router, prefix="/api/v1/sites", tags=["sites"])
app.include_router(groups_router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])



@app.get("/")
def read_root():
    return {"message": "CUCM Portal API is running"}  # נקודת קצה בסיסית שמחזירה הודעת שלום עולם   


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/health/db")
def health_check():

    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
 





