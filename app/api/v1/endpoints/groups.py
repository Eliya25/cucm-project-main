import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.group import Group, SectionGroup, UserGroup
from app.schemas.group import GroupCreate, GroupResponse, UserGroupCreate
from app.core.dependencies import require_admin, get_current_user
from app.models.user import User


router = APIRouter()


@router.post("/", response_model=GroupResponse)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    new_group = Group(**group_data.model_dump(), creator_id=current_user.id) # יצירת אובייקט Group חדש מהנתונים שנשלחו והוספת ה-creator_id

    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


@router.post("/add_user")
def add_user_to_group(data: UserGroupCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    existing = db.query(UserGroup).filter(UserGroup.user_id == data.user_id, UserGroup.group_id == data.group_id).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already in this group")
    
    new_relation = UserGroup(**data.model_dump())
    db.add(new_relation)
    db.commit()
    return {"detail": "User added to group successfully"}


@router.post("/link-site")
def link_group_to_site(site_id: uuid.UUID, group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    new_link = SectionGroup(site_id=site_id, group_id=group_id)

    db.add(new_link)
    db.commit()
    return {"detail": "Group linked to site successfully"}
