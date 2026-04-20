from fastapi import APIRouter, Depends, HTTPException, Response, Request  # נתיבי API וטעינת תלות
from sqlalchemy.orm import Session  # טיפוס session ל-DB
from fastapi.security import OAuth2PasswordRequestForm  # פורמט בקשת התחברות OAuth2
from jose import JWTError

from app.db.session import get_db  # הפונקציה שמייצרת session
from app.models.user import User  # מודל משתמש
from app.models.token_blacklist import TokenBlacklist  # מודל לטוקנים שחורגים   
from app.core.security import verify_password  # וולידציה של סיסמא
from app.core.jwt import create_access_token, create_refresh_token , decode_refresh_token, decode_access_token, get_token_expire  # יצירת tokens
from app.schemas.auth import TokenResponse, LoginRequest  # סכמות של auth
from app.core.dependencies import get_current_user  # תלות של משתמש מאומתn
from logger_manager import LoggerManager

router = APIRouter()  # יצירת ניתוב מודולרי


@router.post("/login", response_model=TokenResponse)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    # מחפש משתמש במאגר לפי שם משתמש
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # לא נמצא משתמש מתאום
        raise HTTPException(status_code=401, detail="Wrong username or password")

    if not user.is_active:
        # משתמש מושבת
        raise HTTPException(status_code=403, detail="User is disabled")

    access_token = create_access_token(data={"sub": str(user.id)})  # יצירת token גישה
    refresh_token = create_refresh_token(data={"sub": str(user.id)})  # יצירת token רענון


    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=1800, secure=False, samesite="lax")  # שמירת token גישה בעוגייה  
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=86400 * 7, secure=False, samesite="strict")  # שמירת token רענון בעוגייה   


    # Audit logging
    LoggerManager.log_audit(
        user=user.username,
        action="LOGIN",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Role: {user.role}"
    )

    return  TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username
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
def refresh_token(request: Request, response: Response, body: LoginRequest | None = None, db: Session = Depends(get_db)):

    token = request.cookies.get("refresh_token")

    if not token and body: 
        token = body.refresh_token
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()

    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked - please log in again")

    try:
        payload = decode_refresh_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        #check if the user stil exists and active
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        #create new access token

        new_access_token = create_access_token(data={"sub": str(user.id)})

        response.set_cookie(key="access_token", value=new_access_token, httponly=True, max_age=1800, secure=False, samesite="lax")  # עדכון עוגיית token גישה עם הטוקן החדש 

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            role=user.role,
            username=user.username,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")
    

@router.post("/logout")
def logout(request: Request, response: Response, body: LoginRequest | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    token = request.cookies.get("refresh_token")

    if not token and body:
        token = body.refresh_token

    if token:
        existing = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()

        if not existing:
            try:
                expires_at = get_token_expire(token)
                blacklisted = TokenBlacklist(token=token, expires_at=expires_at)
                db.add(blacklisted)
                db.commit()
            except JWTError:
                pass  # אם הטוקן לא תקין, פשוט לא נוסיף אותו לשחור


    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    LoggerManager.log_audit(
        user=current_user.username,
        action="LOGOUT",
        target=f"User:{current_user.username} (ID:{current_user.id})",
        details="User logged out and session tokens revoked"
    )

    return {"message": "Logged out successfully"}