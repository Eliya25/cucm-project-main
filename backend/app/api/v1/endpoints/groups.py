import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.group import Group, SectionGroup, UserGroup
from app.models.site import Section, Site
from app.models.roles import UserRole
from app.schemas.group import GroupCreate, GroupResponse, UserGroupCreate
from app.core.dependencies import get_current_user, require_admin, require_super_admin
from app.models.user import User
from logger_manager import LoggerManager

router = APIRouter()


@router.post("/", response_model=GroupResponse)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    existing = db.query(Group).filter(Group.name == group_data.name).first()

    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")

    new_group = Group(**group_data.model_dump(), creator_id=current_user.id)

    db.add(new_group)
    db.flush()
    
    db.add(UserGroup(user_id=current_user.id, group_id=new_group.id))

    db.commit()
    db.refresh(new_group)

    LoggerManager.log_audit(user=current_user.username, action="CREATE_GROUP",
        target=f"Group:{new_group.name} (ID:{new_group.id})", details=f"Description: {new_group.description}")
    return new_group


@router.get("/", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return db.query(Group).all()
    return current_user.groups


@router.get("/me", response_model=list[GroupResponse])
def get_my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if current_user.role == UserRole.SUPERADMIN:
        return db.query(Group).all()
    return current_user.groups


# ── מחיקת Group — SuperAdmin בלבד ────────────────────────────────

@router.delete("/{group_id}", status_code=status.HTTP_200_OK)
def delete_group(group_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    """
    מחיקת Group — SuperAdmin בלבד.
    מוחק גם את כל ה-UserGroup ו-SectionGroup records (CASCADE).
    """
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group_name = group.name

    LoggerManager.log_audit(user=current_user.username, action="DELETE_GROUP",
        target=f"Group:{group.name} (ID:{group.id})",
        details=f"Members: {len(group.user_groups_links)}, Sections: {len(group.section_groups)}")

    db.delete(group)
    db.commit()

    return {"message": f"Group '{group_name}' deleted successfully"}


# ── קישור Site לקבוצה ─────────────────────────────────────────────

@router.post("/link-site")
def link_site_to_group(group_id: uuid.UUID, site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    site = db.query(Site).filter(Site.id == site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    old_group_id = site.group_id

    site.group_id = group_id

    db.commit()

    LoggerManager.log_audit(user=current_user.username, action="LINK_SITE_TO_GROUP",
        target=f"Site:{site.name} → Group:{group.name}", details=f"Previous group: {old_group_id}")

    return {"detail": f"Site '{site.name}' linked to group '{group.name}'"}


# ── קישור Section לקבוצה ──────────────────────────────────────────

@router.post("/{group_id}/link-section")
def link_section_to_group(group_id: uuid.UUID, section_id: uuid.UUID, is_admin: bool = False,db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    existing = db.query(SectionGroup).filter(SectionGroup.section_id == section_id, SectionGroup.group_id == group_id).first()

    if existing:
        existing.is_admin = is_admin
        db.commit()
        return {"detail": "Permissions updated"}

    db.add(SectionGroup(section_id=section_id, group_id=group_id, is_admin=is_admin))

    db.commit()

    LoggerManager.log_audit(user=current_user.username, action="LINK_SECTION_TO_GROUP",
        target=f"Group:{group.name} → Section:{section.name}", details=f"is_admin: {is_admin}")

    return {"detail": f"Section '{section.name}' linked to group '{group.name}'"}


@router.delete("/{group_id}/unlink-section")
def unlink_section_from_group(group_id: uuid.UUID, section_id: uuid.UUID,
                               db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    link = db.query(SectionGroup).filter(SectionGroup.section_id == section_id, SectionGroup.group_id == group_id).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()

    return {"detail": "Section unlinked from group"}


# ── ניהול משתמשים בקבוצה ──────────────────────────────────────────

@router.post("/{group_id}/add-user")
def add_user_to_group(group_id: uuid.UUID, user_id: uuid.UUID,db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user  = db.query(User).filter(User.id == user_id).first()

    group = db.query(Group).filter(Group.id == group_id).first()

    if not user or not group:
        raise HTTPException(status_code=404, detail="User or Group not found")

    existing = db.query(UserGroup).filter(UserGroup.user_id == user_id, UserGroup.group_id == group_id).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already in this group")

    db.add(UserGroup(user_id=user_id, group_id=group_id))

    db.commit()

    LoggerManager.log_audit(user=current_user.username, action="ADD_USER_TO_GROUP",
        target=f"User:{user.username} → Group:{group.name}", details="")

    return {"detail": f"User '{user.username}' added to group '{group.name}'"}


@router.delete("/{group_id}/remove-user")
def remove_user_from_group(group_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):

    user  = db.query(User).filter(User.id == user_id).first()

    group = db.query(Group).filter(Group.id == group_id).first()

    link = db.query(UserGroup).filter(UserGroup.user_id == user_id, UserGroup.group_id == group_id).first()

    if not link:
        raise HTTPException(status_code=404, detail="User is not in this group")

    db.delete(link)
    db.commit()

    LoggerManager.log_audit(user=current_user.username, action="REMOVE_USER_FROM_GROUP",
        target=f"User:{user.username if user else user_id} → Group:{group.name if group else group_id}",
        details="")

    return {"detail": "User removed from group"}