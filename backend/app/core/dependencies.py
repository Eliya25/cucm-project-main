from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
import uuid

from app.db.session import get_db
from app.models.group import SectionGroup, UserGroup
from app.models.user import User, UserRole
from app.core.jwt import decode_access_token

#מה שמפעיל את הכפתור בעצם שמבקש ממני טוקן כדי לאשר שאני
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:

    token = request.cookies.get("access_token") or token  # קודם מנסה לקבל את הטוקן מהעוגייה, אם לא קיים אז מהכותרת Authorization

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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
        raise HTTPException(status_code=403, detail="Super Admin only")
    return current_user

def require_operator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.OPERATOR]:
        raise HTTPException(status_code=403, detail="Operator or Super Admin only")
    return current_user

def validate_section_access(section_id: uuid.UUID, user: User, db: Session):
    
    if user.role == UserRole.SUPERADMIN:
        return True
    
    has_access = db.query(SectionGroup).join(UserGroup, SectionGroup.group_id == UserGroup.group_id).filter(UserGroup.user_id == user.id, SectionGroup.section_id == section_id).first()
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return True