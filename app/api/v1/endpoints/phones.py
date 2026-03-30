from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה

from app.db.session import get_db

from app.core.dependencies import get_current_user, require_operator # הוספנו את get_current_user
from app.models.user import User, UserRole # הוספנו את UserRole לבדיקת תפקיד
from app.schemas.phone import PhoneCreate, PhoneResponse



router = APIRouter()


@router.post("/{section_id}")
def add_phone_to_section(section_id: uuid.UUID, phone_data: PhoneCreate, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):

    existing = db.query(PhoneMapping).filter(PhoneMapping.mac_address == phone_data.mac_address).first()

    if existing:
        raise HTTPException(status_code=400, detail="Phone already mapped in the system")
    
    new_phone = PhoneMapping(
        mac_address=phone_data.mac_address,
        section_id=section_id
    )

    db.add(new_phone)
    db.commit()
    db.refresh(new_phone)

    return new_phone

@router.get("/{section_id}", response_model=list[PhoneResponse])
def get_phones_in_section(section_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #check if the user allowed to see this section
    if current_user.role != UserRole.ADMIN:
        allowed_ids = [section_id for section in current_user.allowed_sections]

        if section_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="You do not have access to this section")
        
    phones = db.query(PhoneMapping).filter(PhoneMapping.section_id == section_id).all()

    return phones
    