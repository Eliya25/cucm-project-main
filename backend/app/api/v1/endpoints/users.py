from fastapi import APIRouter, Depends, HTTPException  # במיוחד להחזרת שגיאות ותלות
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password
from app.core.dependencies import require_admin, require_super_admin
from app.schemas.user import UserCreate, UserResponse
from logger_manager import LoggerManager


router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # שימוש רק למנהל מערכת

    #check if user already exists
    existing = db.query(User).filter(User.username == user_data.username).first()  # בדיקת כפילויות

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),  # יצירת hash סיסמא
        role=user_data.role,
        is_active=True
    )

    db.add(new_user)
    db.commit()  # שמירה למסד
    db.refresh(new_user)  # רענון אובייקט עם ID שנוצר

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_USER",
        target=f"User:{new_user.username} (ID:{new_user.id})",
        details=f"Role: {new_user.role}"
    )

    return new_user  # מוחזר למבקש (נמחקת הסיסמה בגלל מודל response)


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # מנהל יכול לראות את כל המשתמשים
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # מנהל יכול לעדכן username/password/role
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_username = user.username
    old_role = user.role

    user.username = user_data.username or user.username
    if user_data.password:
        user.hashed_password = hash_password(user_data.password)
    user.role = user_data.role or user.role

    db.commit()
    db.refresh(user)

    # Audit logging
    changes = []
    if old_username != user.username:
        changes.append(f"username: {old_username} -> {user.username}")
    if user_data.password:
        changes.append("password changed")
    if old_role != user.role:
        changes.append(f"role: {old_role} -> {user.role}")
    
    LoggerManager.log_audit(
        user=current_user.username,
        action="UPDATE_USER",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Changes: {', '.join(changes)}"
    )

    return user


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    # רק super admin יכול למחוק משתמש
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Audit logging before deletion
    LoggerManager.log_audit(
        user=current_user.username,
        action="DELETE_USER",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Role: {user.role}"
    )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
