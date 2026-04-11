from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה

from app.db.session import get_db
from app.models.site import Site, Section
from app.core.dependencies import require_admin, get_current_user, require_super_admin # הוספנו את get_current_user
from app.models.user import User, UserRole # הוספנו את UserRole לבדיקת תפקיד
from app.schemas.site import SiteCreate, SiteResponse, SectionCreate, SectionResponse
from logger_manager import LoggerManager

router = APIRouter()

# --- פונקציות יצירה (נשארות רק ל-Admin) ---

@router.post("/", response_model=SiteResponse)
def create_site(site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing = db.query(Site).filter(Site.name == site_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists!")
    
    site = Site(name=site_data.name, description=site_data.description)
    db.add(site)
    db.commit()
    db.refresh(site)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_SITE",
        target=f"Site:{site.name} (ID:{site.id})",
        details=f"Description: {site.description}"
    )

    return site

@router.post("/sections", response_model=SectionResponse)
def create_section(section_data: SectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    site = db.query(Site).filter(Site.id == section_data.site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found!")
    
    new_section = Section(**section_data.model_dump())# יצירת אובייקט Section חדש מהנתונים שנשלחו
    db.add(new_section)
    db.commit()
    db.refresh(new_section)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_SECTION",
        target=f"Section:{new_section.name} (ID:{new_section.id})",
        details=f"Site: {site.name}, Description: {new_section.description}"
    )

    return new_section

# --- פונקציות שליפה (מעודכנות עם סינון הרשאות) ---

@router.get("/", response_model=list[SiteResponse])
def get_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. אם המשתמש הוא אדמין - הוא רואה הכל
    if current_user.role == UserRole.SUPERADMIN:
        return db.query(Site).all()
    
    # 2. אם הוא משתמש רגיל - נחזיר רק את האתרים שיש לו הרשאה לפחות לתא אחד בתוכם
    allowed_site_ids = {section.site_id for section in current_user.allowed_sections}

    if not allowed_site_ids:
        return []
    
    return db.query(Site).filter(Site.id.in_(allowed_site_ids)).all()


@router.get("/{site_id}/sections", response_model=list[SectionResponse])
def get_sections(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    site = db.query(Site).filter(Site.id == site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # 1. אם אדמין - רואה את כל התאים באתר
    if current_user.role == UserRole.SUPERADMIN:
        return site.sections
    
    # 2. אם משתמש רגיל - נסנן רק את התאים של האתר הזה שיש לו הרשאה אליהם
    user_sections_in_site = [
        section for section in current_user.allowed_sections 
        if section.site_id == site_id
    ]

    # אם אין למשתמש הרשאה אפילו לתא אחד באתר הזה, נחזיר שגיאה מתאימה
    if not user_sections_in_site:
        raise HTTPException(status_code=403, detail="You don't have permission to view sections in this site")
    
    return user_sections_in_site


@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(site_id: uuid.UUID, site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    old_name = site.name
    old_description = site.description

    site.name = site_data.name or site.name
    site.description = site_data.description or site.description
    db.commit()
    db.refresh(site)

    # Audit logging
    changes = []
    if old_name != site.name:
        changes.append(f"name: {old_name} -> {site.name}")
    if old_description != site.description:
        changes.append(f"description: {old_description} -> {site.description}")
    
    LoggerManager.log_audit(
        user=current_user.username,
        action="UPDATE_SITE",
        target=f"Site:{site.name} (ID:{site.id})",
        details=f"Changes: {', '.join(changes)}"
    )

    return site

@router.delete("/{site_id}")
def delete_site(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    site = db.query(Site).filter(Site.id == site_id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Audit logging before deletion
    LoggerManager.log_audit(
        user=current_user.username,
        action="DELETE_SITE",
        target=f"Site:{site.name} (ID:{site.id})",
        details=f"Description: {site.description}"
    )

    db.delete(site)
    db.commit()
    return {"message": "Site deleted successfully"}