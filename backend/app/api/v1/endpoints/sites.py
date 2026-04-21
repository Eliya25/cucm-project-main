import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.site import Site, Section
from app.models.roles import UserRole
from app.core.dependencies import get_current_user, require_super_admin, require_admin # הוספנו את get_current_user
from app.models.user import User # הוספנו את UserRole לבדיקת תפקיד
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse, SectionCreate, SectionUpdate, SectionResponse
from logger_manager import LoggerManager

router = APIRouter()

# --- פונקציות יצירה (נשארות רק ל-Admin) ---

@router.post("/", response_model=SiteResponse)
def create_site(site_data: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    
    existing = db.query(Site).filter(Site.name == site_data.name).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists!")
    
    site = Site(name=site_data.name, description=site_data.description, group_id=site_data.group_id)

    db.add(site)
    db.commit()
    db.refresh(site)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_SITE",
        target=f"Site:{site.name} (ID:{site.id})",
        details=f"Description: {site.description} Group ID: {site.group_id}"
    )

    return site


@router.get("/", response_model=list[SiteResponse])
def get_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    # 1. אם המשתמש הוא אדמין - הוא רואה הכל
    # if current_user.role == UserRole.SUPERADMIN:

    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]: # אפשר גם לאפשר למנהלים לראות את כל האתרים, לפי הצורך    
        return db.query(Site).all()
    
    allowed_sections = current_user.allowed_sections

    if not allowed_sections:
        return []
    
    allowed_site_ids = {section.site_id for section in allowed_sections}
    return db.query(Site).filter(Site.id.in_(allowed_site_ids)).all()
    
    # 2. אם המשתמש הוא רגיל - הוא רואה רק את האתרים שיש לו גישה אליהם דרך הקבוצות שלו
    # user_group_ids = {link.group_id for link in current_user.user_groups_links}

    # # אם למשתמש אין קבוצות בכלל, נחזיר רשימה ריקה במקום לנסות לבצע שאילתה עם IN על רשימה ריקה   
    # if not user_group_ids:
    #     return []
    
    # # מחזיר את כל האתרים שהקבוצה שלהם נמצאת ברשימת הקבוצות של המשתמש
    # return db.query(Site).filter(Site.group_id.in_(user_group_ids)).all()



@router.get("/{site_id}", response_model=SiteResponse)
def get_site(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    site = db.query(Site).filter(Site.id == site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # 1. אם המשתמש הוא אדמין - הוא רואה הכל
    if not current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]: # אפשר גם לאפשר למנהלים לראות את כל האתרים, לפי הצורך 
        allowed_sections = {section.site_id for section in current_user.allowed_sections}   

        if site.id not in allowed_site_ids:
            raise HTTPException(status_code=403, detail="You don't have permission to view this site")
        return site
    
    # 2. אם המשתמש הוא רגיל - הוא רואה רק את האתרים שיש לו גישה אליהם דרך הקבוצות שלו
    allowed_sections = current_user.allowed_sections

    if not allowed_sections:
        raise HTTPException(status_code=403, detail="You don't have permission to view this site")
    
    allowed_site_ids = {section.site_id for section in allowed_sections}

    if site.id not in allowed_site_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return site


@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(site_id: uuid.UUID, site_data: SiteUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    # רק סופר אדמין יכול לעדכן את פרטי האתר, כולל השם והתיאור שלו. הפונקציה מקבלת את מזהה האתר והנתונים החדשים לעדכון, ומבצעת את העדכון במסד הנתונים. בנוסף, מתבצע רישום של הפעולה ביומן הבקרה (audit log) עם פרטי השינויים שנעשו.
    site = db.query(Site).filter(Site.id == site_id).first()
    # אם האתר לא נמצא, מחזירים שגיאה מתאימה. לאחר העדכון, מתבצע רישום של הפעולה ביומן הבקרה (audit log) עם פרטי השינויים שנעשו, כולל השם והתיאור הישנים והחדשים של האתר. לבסוף, הפונקציה מחזירה את פרטי האתר המעודכנים.
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # שמירת הערכים הישנים לצורך רישום השינויים ביומן הבקרה
    old_name = site.name
    old_description = site.description

    if site_data.name is not None:
        site.name = site_data.name
    if site_data.description is not None:
        site.description = site_data.description
    
    db.commit()
    db.refresh(site)

    # Audit logging
    # יצירת רשומת יומן בקרה עם פרטי השינויים שנעשו בפרטי האתר, כולל השם והתיאור הישנים והחדשים. זה מאפשר מעקב אחר שינויים שנעשו באתר ומי ביצע אותם.
    changes = []
    if old_name != site.name:
        changes.append(f"name: {old_name} -> {site.name}")
    if old_description != site.description:
        changes.append(f"description: {old_description} -> {site.description}")
    
    # רישום הפעולה ביומן הבקרה עם פרטי השינויים שנעשו בפרטי האתר, כולל השם והתיאור הישנים והחדשים. זה מאפשר מעקב אחר שינויים שנעשו באתר ומי ביצע אותם.
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

    return {"message": f"Site '{site.name}' and all its sections deleted successfully"}


# ══════════════════════════════════════════════════════
#  SECTIONS
# ══════════════════════════════════════════════════════

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

@router.get("/{site_id}/sections", response_model=list[SectionResponse])
def get_sections(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    site = db.query(Site).filter(Site.id == site_id).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # 1. אם אדמין - רואה את כל התאים באתר
    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]: # אפשר גם לאפשר למנהלים לראות את כל התאים, לפי הצורך 
        return site.sections
    
    # 2. אם משתמש רגיל - נסנן רק את התאים של האתר הזה שיש לו הרשאה אליהם
    user_sections_in_site = [
        section for section in current_user.allowed_sections 
        if section.site_id == site_id
    ]

    # אם אין למשתמש הרשאה אפילו לתא אחד באתר הזה, נחזיר שגיאה מתאימה
    if not user_sections_in_site:
        raise HTTPException(status_code=403, detail="You have no access to any sections in this site")
    
    return user_sections_in_site


@router.patch("/sections/{section_id}", response_model=SectionResponse)
def update_section(section_id: uuid.UUID, section_data: SectionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):

    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    old_name = section.name
    section.name = section_data.name or section.name
    section.description = section_data.description or section.description

    db.commit()
    db.refresh(section)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="UPDATE_SECTION",
        target=f"Section:{section.name} (ID:{section.id})",
        details=f"Changes: name: {old_name} -> {section.name}, description: {section.description}"
    )

    return section

@router.delete("/sections/{section_id}")
def delete_section(section_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):

    section = db.query(Section).filter(Section.id == section_id).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Audit logging before deletion
    LoggerManager.log_audit(
        user=current_user.username,
        action="DELETE_SECTION",
        target=f"Section:{section.name} (ID:{section.id})",
        details=f"Description: {section.site_id} (related site: {section.site.name})"
    )

    db.delete(section)
    db.commit()

    return {"message": f"Section '{section.name}' deleted successfully"}



