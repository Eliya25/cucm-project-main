import uuid
from fastapi import APIRouter, Depends, HTTPException  # במיוחד להחזרת שגיאות ותלות
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.roles import UserRole
from app.core.security import hash_password
from app.core.dependencies import require_super_admin, require_admin, get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from logger_manager import LoggerManager


router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # שימוש רק למנהל מערכת

    if user_data.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="you cannot create a super admin user")

    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can create admin users")
    
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

    if current_user.role == UserRole.SUPERADMIN:
        # מנהל יכול לראות את כל המשתמשים
        return db.query(User).all()
    
    return db.query(User).filter(User.role != UserRole.SUPERADMIN).all()  # אדמין לא רואה משתמשים שהם סופר אדמין    

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="You don't have permission to view this user")

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, user_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    # מנהל יכול לעדכן username/password/role
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify super admin user")
    
    if user_data.role in [UserRole.ADMIN, UserRole.SUPERADMIN] and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only super admin can assign elevated roles")

    old_role = user.role

    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)

    if user_data.role is not None:
        user.role = user_data.role

    if user_data.is_active is not None:
        if user.id == current_user.id:
            raise HTTPException(status_code=403, detail="You cannot change your own active status")
        user.is_active = user_data.is_active


    db.commit()
    db.refresh(user)

    # Audit logging
    changes = []
    if user_data.password:
        changes.append("password changed")
    if user_data.role and old_role != user.role:
        changes.append(f"role: {old_role} -> {user.role}")
    if user_data.is_active is not None:
        changes.append(f"active status: {user.is_active}")

    
    LoggerManager.log_audit(
        user=current_user.username,
        action="UPDATE_USER",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Changes: {', '.join(changes)}"
    )

    return user


@router.delete("/{user_id}")
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    # רק super admin יכול למחוק משתמש
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own user")
    
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete super admin user")
    
    if current_user.role == UserRole.ADMIN and user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin users cannot delete other admin users")
    
    # Audit logging before deletion
    LoggerManager.log_audit(
        user=current_user.username,
        action="DELETE_USER",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"Role: {user.role}"
    )

    db.delete(user)
    db.commit()

    return {"message": f"User '{user.username}' deleted successfully"}

@router.patch("/{user_id}/toggle-active")
def toogle_active(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own active status")
    
    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot change active status of super admin user")
    

    user.is_active = not user.is_active

    db.commit()


    status = "activated" if user.is_active else "deactivated"
   
    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="TOGGLE_USER_ACTIVE",
        target=f"User:{user.username} (ID:{user.id})",
        details=f"User {status}"
    )

    return {"message": f"User '{user.username}' {status}", "is_active": user.is_active}