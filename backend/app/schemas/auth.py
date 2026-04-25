from pydantic import BaseModel
from app.models.roles import UserRole


class TokenResponse(BaseModel):  # תשובת טוקן
    access_token: str  # טוקן JWT לשימוש בקריאות מוגנות
    token_type: str = "bearer"  # סוג האימות
    username: str  # שם המשתמש של המשתמש המחובר
    role: UserRole  # תפקיד המשתמש (SUPERADMIN, ADMIN, OPERATOR או VIEWER)