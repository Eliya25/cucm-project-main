from pydantic import BaseModel

class LoginRequest(BaseModel):  # בקשת התחברות
    username: str  # שם משתמש
    password: str  # סיסמה


class TokenResponse(BaseModel):  # תשובת טוקן
    access_token: str  # טוקן JWT לשימוש בקריאות מוגנות
    refresh_token: str  # טוקן רענון
    token_type: str = "bearer"  # סוג האימות

