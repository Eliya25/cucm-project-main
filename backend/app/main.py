import sys
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.sites import router as sites_router
from app.api.v1.endpoints.groups import router as groups_router
from app.api.v1.endpoints.devices import router as devices_router

# חשוב: כל המודלים חייבים להיטען לפני create_all
import app.models.user
import app.models.site
import app.models.device
import app.models.group
import app.models.token_blacklist

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_manager import LoggerManager
from app.core.jwt import decode_access_token
from app.models.user import User

# יצירת טבלאות חדשות אם לא קיימות (לא מחליף alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CUCM Portal API", description="Phone management system for CUCM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    LoggerManager.initialize(path_prefix="logs")
    LoggerManager.get_logger().info("-- CUCM Portal started --")


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

    user_info = _get_user_info_from_request(request)
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)

    log_msg = (
        f"[{request.method}] {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Time: {process_time}ms | "
        f"IP: {request.client.host} | "
        f"User: {user_info}"
    )

    if response.status_code >= 400:
        logger.error(log_msg)
    else:
        logger.info(log_msg)

    return response


app.include_router(auth_router,    prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(users_router,   prefix="/api/v1/users",   tags=["Users"])
app.include_router(sites_router,   prefix="/api/v1/sites",   tags=["Sites"])
app.include_router(groups_router,  prefix="/api/v1/groups",  tags=["Groups"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])


@app.get("/")
def read_root():
    return {"message": "CUCM Portal API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def db_health_check():
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")