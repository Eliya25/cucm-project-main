import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.group import Group, SectionGroup, UserGroup
from app.schemas.group import GroupCreate, GroupResponse, UserGroupCreate
from app.core.dependencies import require_admin, get_current_user
from app.models.user import User
from logger_manager import LoggerManager

router = APIRouter()


@router.post("/link-section")
def link_group_to_section(section_id: uuid.UUID, group_id: uuid.UUID, is_admin: bool = False,  db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # בדיקה אם הקישור כבר קיים בין הקבוצה לתא, ואם כן - עדכון סטטוס האדמין שלו בהתאם לפרמטר שנשלח, ואם לא - יצירת הקישור עם הסטטוס המתאים
    existing = db.query(SectionGroup).filter(SectionGroup.section_id == section_id, SectionGroup.group_id == group_id).first()

    # אם הקישור כבר קיים, נעדכן את סטטוס האדמין שלו בהתאם לפרמטר שנשלח (אפשר לשנות את הסטטוס גם אם הקישור כבר קיים)
    if existing:
        existing.is_admin = is_admin # עדכון סטטוס אדמין אם הקישור כבר קיים
        db.commit()
        return {"detail": "Group permissions updated for the section"}
    
    # אם הקישור לא קיים, ניצור אותו עם הסטטוס המתאים
    new_link = SectionGroup(section_id=section_id, group_id=group_id, is_admin=is_admin)
    db.add(new_link)
    db.commit()
    return {"detail": "Group linked to section successfully"}

@router.post("/", response_model=GroupResponse)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    new_group = Group(**group_data.model_dump(), creator_id=current_user.id) # יצירת אובייקט Group חדש מהנתונים שנשלחו והוספת ה-creator_id

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_GROUP",
        target=f"Group:{new_group.name} (ID:{new_group.id})",
        details=f"Description: {new_group.description}"
    )

    return new_group


@router.post("/add_user")
def add_user_to_group(data: UserGroupCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # בדיקה אם המשתמש והקבוצה קיימים, ואם כן - יצירת הקשר ביניהם בטבלת UserGroup, ואם לא - החזרת שגיאה מתאימה
    user_exists = db.query(User).filter(User.id == data.user_id).first()
    # בדיקה אם הקבוצה קיימת, אם לא - החזרת שגיאה מתאימה
    group_exists = db.query(Group).filter(Group.id == data.group_id).first()

    # אם המשתמש או הקבוצה לא קיימים, נחזיר שגיאה מתאימה
    if not user_exists or not group_exists:
        raise HTTPException(status_code=404, detail="User or Group not found")

    # בדיקה אם הקשר כבר קיים בין המשתמש לקבוצה, אם כן - החזרת שגיאה מתאימה
    existing = db.query(UserGroup).filter(UserGroup.user_id == data.user_id, UserGroup.group_id == data.group_id).first()

    # אם הקשר כבר קיים, נחזיר שגיאה מתאימה
    if existing:
        raise HTTPException(status_code=400, detail="User already in this group")
    
    # אם הכל תקין, ניצור את הקשר בין המשתמש לקבוצה בטבלת UserGroup
    new_relation = UserGroup(user_id=data.user_id, group_id=data.group_id)

    # הוספת הקשר למסד נתונים ולבסוף החזרת תשובה מתאימה
    db.add(new_relation)
    # שליחת השינויים למסד נתונים כדי לשמור את הקשר החדש בין המשתמש לקבוצה ולוודא שהמידע מעודכן לפני החזרת התשובה
    db.commit()

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="ADD_USER_TO_GROUP",
        target=f"User:{user_exists.username} -> Group:{group_exists.name}",
        details=f"User ID: {data.user_id}, Group ID: {data.group_id}"
    )

    return {"detail": "User added to group successfully"}


@router.post("/link-site")
def link_group_to_site(site_id: uuid.UUID, group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    new_link = SectionGroup(site_id=site_id, group_id=group_id)

    db.add(new_link)
    db.commit()
    return {"detail": "Group linked to site successfully"}

@router.get("/me", response_model=list[GroupResponse])
def get_my_groups(current_user: User = Depends(get_current_user)):
    return current_user.groups