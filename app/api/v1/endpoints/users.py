from fastapi import APIRouter, Depends, HTTPException  # במיוחד להחזרת שגיאות ותלות
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserSection
from app.models.site import Section
from app.core.security import hash_password
from app.core.dependencies import require_admin, require_super_admin
from app.schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # שימוש רק למנהל מערכת

    #check if user already exists
    existing = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()  # בדיקת כפילויות

    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    sections =  db.query(Section).filter(Section.id.in_(user_data.section_ids)).all()

    if len(sections) != len(user_data.section_ids):
        raise HTTPException(status_code=400, detail="One or more sections not found!")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),  # יצירת hash סיסמא
        role=user_data.role,
        is_active=True
    )

    new_user.allowed_sections = sections

    db.add(new_user)
    db.commit()  # שמירה למסד
    db.refresh(new_user)  # רענון אובייקט עם ID שנוצר

    return new_user  # מוחזר למבקש (נמחקת הסיסמה בגלל מודל response)


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # מנהל יכול לראות את כל המשתמשים
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # מנהל יכול לעדכן role/sections
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = user_data.username or user.username
    user.email = user_data.email or user.email
    if user_data.password:
        user.hashed_password = hash_password(user_data.password)
    user.role = user_data.role or user.role

    requested_section_ids = []
    if user_data.section_id:
        requested_section_ids.append(user_data.section_id)
    if user_data.section_ids:
        requested_section_ids.extend(user_data.section_ids)

    requested_section_ids = list(dict.fromkeys(requested_section_ids))

    if requested_section_ids:
        sections = db.query(Section).filter(Section.id.in_(requested_section_ids)).all()
        if len(sections) != len(requested_section_ids):
            raise HTTPException(status_code=400, detail="One or more sections not found!")
        user.allowed_sections = sections
        user.section_id = sections[0].id if sections else None

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    # רק super admin יכול למחוק משתמש
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return None
