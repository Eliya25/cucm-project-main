from pydantic import BaseModel
from app.models.roles import UserRole

class LoginRequest(BaseModel):  # בקשת התחברות
    username: str  # שם משתמש
    password: str  # סיסמה
    refresh_token: str | None = None
#צריך לבדוק מה קורה

class TokenResponse(BaseModel):  # תשובת טוקן
    access_token: str  # טוקן JWT לשימוש בקריאות מוגנות
    token_type: str = "bearer"  # סוג האימות
    username: str  # שם המשתמש של המשתמש המחובר
    role: UserRole  # תפקיד המשתמש (SUPERADMIN, ADMIN, OPERATOR או VIEWER)

class RefreshTokenRequest(BaseModel):  # בקשת טוקן רענון    
    refresh_token: str  # טוקן רענון לשימוש בקבלת טוקן חדש  