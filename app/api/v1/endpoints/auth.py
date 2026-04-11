from fastapi import APIRouter, Depends, HTTPException  # נתיבי API וטעינת תלות
from sqlalchemy.orm import Session  # טיפוס session ל-DB
from fastapi.security import OAuth2PasswordRequestForm  # פורמט בקשת התחברות OAuth2
from jose import JWTError

from app.db.session import get_db  # הפונקציה שמייצרת session
from app.models.user import User  # מודל משתמש
from app.core.security import verify_password  # וולידציה של סיסמא
from app.core.jwt import create_access_token, create_refresh_token  # יצירת tokens
from app.schemas.auth import TokenResponse  # סכמות של auth
from app.core.dependencies import get_current_user  # תלות של משתמש מאומת
from app.core.jwt import decoded_refresh_token, create_access_token
from logger_manager import LoggerManager

router = APIRouter()  # יצירת ניתוב מודולרי


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # מחפש משתמש במאגר לפי שם משתמש
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        # לא נמצא משתמש מתאום
        raise HTTPException(status_code=401, detail="Wrong username or password")

    if not verify_password(form_data.password, user.hashed_password):
        # סיסמה אינה נכונה
        raise HTTPException(status_code=401, detail="Wrong username or password")

    if not user.is_active:
        # משתמש מושבת
        raise HTTPException(status_code=403, detail="User is disabled")

    access_token = create_access_token(data={"sub": str(user.id)})  # יצירת token גישה
    refresh_token = create_refresh_token(data={"sub": str(user.id)})  # יצירת token רענון

    # Audit logging
    LoggerManager.log_audit(
        user=user.username,
        action="LOGIN",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Role: {user.role}"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    # מחזיר מידע בסיסי על המשתמש הנוכחי
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):

    try:
        payload = decoded_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        #check if the user stil exists and active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        #create new access token

        new_access_token = create_access_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")