from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.roles import UserRole
from app.core.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    
    cookie_token = request.cookies.get("access_token")
    resolved_token = cookie_token or token  # cookie קודם, אחר כך Authorization header

    if not resolved_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(resolved_token)
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

    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="SuperAdmin access required")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:

    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_operator(current_user: User = Depends(get_current_user)) -> User:

    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.OPERATOR]:
        raise HTTPException(status_code=403, detail="Operator access required")
    
    return current_user


def validate_section_access(section_id: uuid.UUID, user: User, db: Session) -> bool:

    if user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return True
    
    if not user.has_section_access(section_id):
        raise HTTPException(status_code=403, detail="Access denied to this section")
    
    return True