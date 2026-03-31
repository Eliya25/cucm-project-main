from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.jwt import decode_access_token

#מה שמפעיל את הכפתור בעצם שמבקש ממני טוקן כדי לאשר שאני
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    
    return user

def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    #check that is the really the super admin
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="This action allow only for super admin")
    
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user

def require_operator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.OPERATOR]:
        raise HTTPException(status_code=403, detail="Operator or Admin only")
    return current_user