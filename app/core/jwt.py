from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINTUES = 30  # זמן חיי טוקן גישה בדקות
REFRESH_TOKEN_EXPIRE_DAYS = 7  # זמן חיי טוקן רענון בימים


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINTUES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data:dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload

def decoded_refresh_token(token:str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload
