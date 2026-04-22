from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from app.db.session import get_db
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.core.security import verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_refresh_token, get_token_expire
from app.schemas.auth import TokenResponse, LogoutRequest, RefreshTokenRequest
from app.core.dependencies import get_current_user
from logger_manager import LoggerManager

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # שני הטוקנים יושבים ב-httponly cookies - לא חשופים ל-JavaScript
    response.set_cookie(key="access_token",  value=access_token,  httponly=True, max_age=1800,      secure=False, samesite="lax")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=86400 * 7, secure=False, samesite="strict")

    LoggerManager.log_audit(
        user=user.username, 
        action="LOGIN",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Role: {user.role}"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db)
):
    # קודם cookie, אחר כך body
    token = request.cookies.get("refresh_token")
    if not token and body:
        token = body.refresh_token
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    # בדיקה שהטוקן לא בוטל
    blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()

    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked - please log in again")

    try:
        payload = decode_refresh_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        new_access_token = create_access_token(data={"sub": str(user.id)})

        response.set_cookie(key="access_token", value=new_access_token, httponly=True, max_age=1800, secure=False, samesite="lax")


        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            role=user.role,
            username=user.username
        )
    
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # קודם cookie, אחר כך body
    token = request.cookies.get("refresh_token")

    if token:
        existing = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        
        if not existing:
            try:
                expires_at = get_token_expire(token)
                db.add(TokenBlacklist(token=token, expires_at=expires_at))
                db.commit()
            except JWTError:
                pass  

    # מחיקת cookies בכל מקרה
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    LoggerManager.log_audit(
        user=current_user.username, 
        action="LOGOUT",
        target=f"User:{current_user.username} (ID:{current_user.id})",
        details="Session terminated"
    )

    return {"message": "Logged out successfully"}