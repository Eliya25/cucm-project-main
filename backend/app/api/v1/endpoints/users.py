import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.roles import UserRole
from app.core.security import hash_password, verify_password
from app.core.dependencies import require_admin, get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate, ChangePasswordRequest
from logger_manager import LoggerManager

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    if user_data.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot create SuperAdmin via API")

    if user_data.role == UserRole.ADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only SuperAdmin can create Admin users")

    existing = db.query(User).filter(User.username == user_data.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    LoggerManager.log_audit(user=current_user.username, action="CREATE_USER",
        target=f"User:{new_user.username} (ID:{new_user.id})", details=f"Role: {new_user.role}")

    return new_user


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    if current_user.role == UserRole.SUPERADMIN:
        return db.query(User).all()

    return db.query(User).filter(User.role != UserRole.SUPERADMIN).all()




@router.patch("/me/change-password")
def change_my_password(body: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    current_user.hashed_password = hash_password(body.new_password)

    db.commit()

    LoggerManager.log_audit(user=current_user.username, action="CHANGE_PASSWORD",
        target=f"User:{current_user.username} (ID:{current_user.id})", details="Password changed")
    return {"message": "Password changed successfully"}


# ── /{user_id} routes ─────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, user_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify SuperAdmin")

    if user_data.role in [UserRole.ADMIN, UserRole.SUPERADMIN] and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only SuperAdmin can assign elevated roles")

    old_role = user.role

    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot change your own active status")
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    changes = []
    if user_data.password: changes.append("password changed")
    if user_data.role and old_role != user.role: changes.append(f"role: {old_role} → {user.role}")

    LoggerManager.log_audit(user=current_user.username, action="UPDATE_USER",
        target=f"User:{user.username} (ID:{user.id})", details=f"Changes: {', '.join(changes)}")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete SuperAdmin")

    if current_user.role == UserRole.ADMIN and user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins cannot delete other Admins")

    username = user.username

    LoggerManager.log_audit(user=current_user.username, action="DELETE_USER",
        target=f"User:{user.username} (ID:{user.id})", details=f"Role: {user.role}")

    db.delete(user)
    db.commit()

    return {"message": f"User '{username}' deleted successfully"}


@router.patch("/{user_id}/toggle-active")
def toggle_active(user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own active status")

    if user.role == UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Cannot deactivate SuperAdmin")

    user.is_active = not user.is_active

    db.commit()

    status_str = "activated" if user.is_active else "deactivated"

    LoggerManager.log_audit(user=current_user.username, action="TOGGLE_USER_ACTIVE",
        target=f"User:{user.username} (ID:{user.id})", details=f"User {status_str}")
        
    return {"message": f"User '{user.username}' {status_str}", "is_active": user.is_active}