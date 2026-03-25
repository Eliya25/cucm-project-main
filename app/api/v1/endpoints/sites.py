from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה

from app.db.session import get_db
from app.models.site import Site, Section
from app.core.dependencies import require_admin, get_current_user, require_super_admin # הוספנו את get_current_user
from app.models.user import User, UserRole # הוספנו את UserRole לבדיקת תפקיד
from app.schemas.site import SiteCreate, SiteResponse, SectionCreate, SectionResponse

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
    return site

@router.post("/sections", response_model=SectionResponse)
def create_section(section_data: SectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    site = db.query(Site).filter(Site.id == section_data.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found!")
    
    section = Section(name=section_data.name, site_id=section_data.site_id)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section

# --- פונקציות שליפה (מעודכנות עם סינון הרשאות) ---

@router.get("/", response_model=list[SiteResponse])
def get_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. אם המשתמש הוא אדמין - הוא רואה הכל
    if current_user.role == UserRole.ADMIN:
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
    if current_user.role == UserRole.ADMIN:
        return site.sections
    
    # 2. אם משתמש רגיל - נסנן רק את התאים של האתר הזה שיש לו הרשאה אליהם
    user_sections_in_site = [
        section for section in current_user.allowed_sections 
        if section.site_id == site_id
    ]
    
    return user_sections_in_site


@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(site_id: uuid.UUID, site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.name = site_data.name or site.name
    site.description = site_data.description or site.description
    db.commit()
    db.refresh(site)
    return site

@router.delete("/{site_id}", status_code=204)
def delete_site(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    db.delete(site)
    db.commit()
    return None