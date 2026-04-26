import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.device import DevicePosition, Device
from app.models.roles import UserRole
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.core.dependencies import get_current_user, require_operator # הוספנו את get_current_user
from app.models.user import User
from logger_manager import LoggerManager





router = APIRouter()


@router.get("/", response_model=list[DeviceResponse])
def get_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #השתמשנו ב-joinedload כדי לטעון מראש את המידע על ה-section של כל מכשיר
    # , כך שנוכל לבדוק את ההרשאות של המשתמש על ה-section הזה בלי צורך בשאילתות נוספות למסד נתונים עבור כל מכשיר בנפרד
    query = db.query(Device).options(joinedload(Device.section))

    #check if the user allowed to see this section
    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]: # אפשר גם לאפשר למנהלים לראות את כל המכשירים, לפי הצורך  
       return query.all()
    
    # אם המשתמש הוא אופרטור, נחזיר רק את המכשירים שה-section שלהם נמצא ברשימת ה-allowed_section_ids של המשתמש   
    allowed_section_ids = list(current_user.allowed_section_ids)

    if not allowed_section_ids:
        return [] # אם אין למשתמש הרשאה אפילו לתא אחד, נחזיר רשימה ריקה במקום לנסות להריץ שאילתה עם רשימת מזהים ריקה שתחזיר שגיאה   

    return query.filter(Device.section_id.in_(allowed_section_ids)).all()# נחזיר רק את המכשירים שה-section שלהם נמצא ברשימת ה-allowed_section_ids של המשתמש


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    #check if the user allowed to see this section
    if not current_user.has_section_access(device.section_id): # אפשר גם לאפשר למנהלים לראות את כל המכשירים, לפי הצורך  
       raise HTTPException(status_code=403, detail="Access denied to this device")
    
    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(device_data: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    if not current_user.is_admin_of_section(device_data.section_id):
        raise HTTPException(status_code=403, detail="You don't have permission to add devices to this section")
 
    existing = db.query(Device).filter(Device.identifier == device_data.identifier).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this identifier already exists")
 
    new_device = Device(**device_data.model_dump())
    db.add(new_device)
    db.flush()
 
    db.add(DevicePosition(device_id=new_device.id, x_pos=0.0, y_pos=0.0))
    db.commit()
    db.refresh(new_device)
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="CREATE_DEVICE",
        target=f"Device:{new_device.identifier} (ID:{new_device.id})",
        details=f"Section ID: {new_device.section_id}"
    )

    return new_device

@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: uuid.UUID, device_data: DeviceUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
 
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have admin permission to update devices in this section")
 
    update_data = device_data.model_dump(exclude_unset=True)

    old_identifier = device.identifier
    old_classification = device.classification
 
    for field in ["identifier", "classification"]:
        if field in update_data:
            setattr(device, field, update_data[field])
 
    if "x_pos" in update_data or "y_pos" in update_data:
        position = db.query(DevicePosition).filter(DevicePosition.device_id == device_id).first()

        if not position:
            position = DevicePosition(device_id=device_id, x_pos=0.0, y_pos=0.0)
            db.add(position)

        if "x_pos" in update_data:
            position.x_pos = update_data["x_pos"]
        if "y_pos" in update_data:
            position.y_pos = update_data["y_pos"]
 
    db.commit()
    db.refresh(device)
 
    changes = []

    if old_identifier != device.identifier:
        changes.append(f"identifier: {old_identifier} → {device.identifier}")
    if old_classification != device.classification:
        changes.append(f"classification: {old_classification} → {device.classification}")
    if "x_pos" in update_data or "y_pos" in update_data:
        changes.append("position updated")
 
    if changes:
        LoggerManager.log_audit(
            user=current_user.username, 
            action="UPDATE_DEVICE",
            target=f"Device:{device.identifier} (ID:{device.id})",
            details=f"Changes: {', '.join(changes)}"
        )

    return device


@router.put("/{device_id}/position")
def update_device_position(device_id: uuid.UUID, x: float, y: float, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
   
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
 
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have admin permission to update position")
 
    position = db.query(DevicePosition).filter(DevicePosition.device_id == device_id).first()

    if not position:
        position = DevicePosition(device_id=device_id, x_pos=x, y_pos=y)
        db.add(position)
    else:
        position.x_pos = x
        position.y_pos = y
 
    db.commit()
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="UPDATE_DEVICE_POSITION",
        target=f"Device:{device.identifier} (ID:{device.id})",
        details=f"New position: x={x}, y={y}"
    )

    return {"status": "success", "device_id": device_id, "new_position": {"x": x, "y": y}}
 

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
 
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have admin permission to delete devices in this section")
 
    LoggerManager.log_audit(
        user=current_user.username, 
        action="DELETE_DEVICE",
        target=f"Device:{device.identifier} (ID:{device.id})",
        details=f"Section ID: {device.section_id}"
    )
    
    db.delete(device)
    db.commit()

    return {"message": "Device deleted successfully"}