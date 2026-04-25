import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.site import Site, Section
from app.models.roles import UserRole
from app.core.dependencies import get_current_user, require_super_admin, require_admin 
from app.models.user import User 
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse, SectionCreate, SectionUpdate, SectionResponse
from logger_manager import LoggerManager

router = APIRouter()

# --- פונקציות יצירה (נשארות רק ל-Admin) ---

# ══════════════════════════════════════════════════════
#  SITES
# ══════════════════════════════════════════════════════

@router.post("/", response_model=SiteResponse)
def create_site(site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing = db.query(Site).filter(Site.name == site_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists")
 
    site = Site(name=site_data.name, description=site_data.description, group_id=site_data.group_id)
    db.add(site)
    db.commit()
    db.refresh(site)
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="CREATE_SITE",
        target=f"Site:{site.name} (ID:{site.id})", 
        details=f"Group ID: {site.group_id}"
    )
    
    return site


@router.get("/", response_model=list[SiteResponse])
def get_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return db.query(Site).all()
 
    allowed_sections = current_user.allowed_sections
    if not allowed_sections:
        return []
 
    allowed_site_ids = {s.site_id for s in allowed_sections}
    return db.query(Site).filter(Site.id.in_(allowed_site_ids)).all()



# ══════════════════════════════════════════════════════
#  SECTIONS
# ══════════════════════════════════════════════════════

@router.post("/sections", response_model=SectionResponse)
def create_section(section_data: SectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    site = db.query(Site).filter(Site.id == section_data.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
 
    new_section = Section(**section_data.model_dump())
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="CREATE_SECTION",
        target=f"Section:{new_section.name} (ID:{new_section.id})", 
        details=f"Site: {site.name}"
    )

    return new_section


# --- פונקציות שליפה (מעודכנות עם סינון הרשאות) ---

@router.get("/{site_id}/sections", response_model=list[SectionResponse])
def get_sections(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    site = db.query(Site).filter(Site.id == site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
 
    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return site.sections
 
    user_sections_in_site = [s for s in current_user.allowed_sections if s.site_id == site_id]

    if not user_sections_in_site:
        raise HTTPException(status_code=403, detail="No access to any section in this site")
    
    return user_sections_in_site

@router.patch("/sections/{section_id}", response_model=SectionResponse)
def update_section(section_id: uuid.UUID, section_data: SectionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
 
    old_name = section.name
 
    # תוקן: שימוש ב-is not None במקום or - מונע איפוס שדה לערך ריק
    if section_data.name is not None:
        section.name = section_data.name
    if section_data.description is not None:
        section.description = section_data.description
 
    db.commit()
    db.refresh(section)
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="UPDATE_SECTION",
        target=f"Section:{section.name} (ID:{section.id})", 
        details=f"name: {old_name} → {section.name}"
    )

    return section

@router.delete("/sections/{section_id}")
def delete_section(section_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
 
    LoggerManager.log_audit(user=current_user.username, action="DELETE_SECTION",
        target=f"Section:{section.name} (ID:{section.id})", details=f"Site ID: {section.site_id}")
    db.delete(section)
    db.commit()
    return {"message": f"Section '{section.name}' deleted successfully"}
 



@router.get("/{site_id}", response_model=SiteResponse)
def get_site(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
 
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        allowed_site_ids = {s.site_id for s in current_user.allowed_sections}
        if site_id not in allowed_site_ids:
            raise HTTPException(status_code=403, detail="Access denied")
 
    return site


@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(site_id: uuid.UUID, site_data: SiteUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
 
    old_name, old_desc = site.name, site.description
 
    if site_data.name is not None:
        site.name = site_data.name
    if site_data.description is not None:
        site.description = site_data.description
 
    db.commit()
    db.refresh(site)
 
    changes = []
    if old_name != site.name: changes.append(f"name: {old_name} → {site.name}")
    if old_desc != site.description: changes.append("description updated")
 
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
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="DELETE_SITE",
        target=f"Site:{site.name} (ID:{site.id})", 
        details=f"Description: {site.description}"
    )

    db.delete(site)
    db.commit()

    return {"message": f"Site '{site.name}' and all its sections deleted successfully"}
 
 


