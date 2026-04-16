from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import uuid # הוספנו כדי לטפל ב-UUID בצורה נכונה
from app.db.session import get_db
from app.models.device import DevicePosition, Device
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.core.dependencies import get_current_user, require_admin # הוספנו את get_current_user
from app.models.user import User, UserRole # הוספנו את UserRole לבדיקת תפקיד
from logger_manager import LoggerManager





router = APIRouter()


@router.get("/", response_model=list[DeviceResponse])
def get_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #השתמשנו ב-joinedload כדי לטעון מראש את המידע על ה-section של כל מכשיר
    # , כך שנוכל לבדוק את ההרשאות של המשתמש על ה-section הזה בלי צורך בשאילתות נוספות למסד נתונים עבור כל מכשיר בנפרד
    query = db.query(Device).options(joinedload(Device.section))

    #check if the user allowed to see this section
    if current_user.role == UserRole.SUPERADMIN:
       return query.all()
    
    #אם המשתמש לא אדמין, נחזיר רק את המכשירים שנמצאים בתא שהם מורשים אליו לפחות
    allowed_section_ids = [section.id for section in current_user.allowed_sections]

    return query.filter(Device.section_id.in_(allowed_section_ids)).all()# נחזיר רק את המכשירים שה-section שלהם נמצא ברשימת ה-allowed_section_ids של המשתמש




@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(device_data: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #בדיקה אם המשתמש הוא אדמין של התא שאליו מנסים להוסיף את המכשיר, אם לא נחזיר שגיאה מתאימה
    if not current_user.is_admin_of_section(device_data.section_id):
        raise HTTPException(status_code=403, detail="You don't have permission to add devices to this section")

    new_device = Device(**device_data.model_dump()) # יצירת אובייקט Device חדש מהנתונים שנשלחו

    db.add(new_device)
    db.flush() # שליחת השינויים למסד נתונים כדי לקבל את ה-ID שנוצר למכשיר החדש לפני יצירת רשומת המיקום שלו
    initial_position = DevicePosition(device_id=new_device.id, x_pos=0.0, y_pos=0.0) # יצירת רשומת מיקום ראשונית עם קואורדינטות ברירת מחדל (0,0)
    db.add(initial_position)

    db.commit()
    db.refresh(new_device)

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="CREATE_DEVICE",
        target=f"Device:{new_device.identifier} (ID:{new_device.id})",
        details=f"Section ID: {new_device.section_id}, Classification: {new_device.classification}"
    )

    return new_device

@router.patch("/{device_id}", response_model=DeviceResponse)# פונקציה לעדכון פרטי המכשיר, כולל המיקום שלו
def update_device(device_id: uuid.UUID, device_data: DeviceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #find the device
    device = db.query(Device).filter(Device.id == device_id).first()

    #אם המכשיר לא נמצא, נחזיר שגיאה מתאימה
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    #check if the user has permission to update the device (must be admin of the section that the device belongs to)
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have permission to update devices in this section")
    
    #השתמשנו ב-model_dump עם exclude_unset כדי לקבל רק את השדות שנשלחו בבקשה לעדכון, וכך נוכל לעדכן רק את השדות האלה מבלי לגעת בשאר השדות של המכשיר
    update_data = device_data.model_dump(exclude_unset=True)

    old_identifier = device.identifier
    old_classification = device.classification

    #עדכון שדות המכשיר הרגילים (identifier ו-classification) רק אם הם נשלחו בבקשה, אם לא הם יישארו ללא שינוי
    for field in ["identifier", "classification"]:
        if field in update_data:
            setattr(device, field, update_data[field])

    #אם נשלחו נתוני מיקום בעדכון, נטפל בהם בנפרד כי הם נמצאים בטבלה נפרדת
    if "x_pos" in update_data or "y_pos" in update_data:
        position = db.query(DevicePosition).filter(DevicePosition.device_id == device_id).first()

        #אם אין עדיין רשומה של מיקום למכשיר הזה, ניצור אחת חדשה עם המיקום החדש (או ברירת מחדל אם אחד מהקואורדינטות לא נשלח)
        if not position:
            position = DevicePosition(device_id=device_id, x_pos=0, y_pos=0) # יצירת רשומה חדשה עם מיקום ברירת מחדל אם לא קיימת
            db.add(position)
        
        #עדכון שדות המיקום רק אם הם נשלחו בבקשה
        if "x_pos" in update_data:
            position.x_pos = update_data["x_pos"]
        if "y_pos" in update_data:
            position.y_pos = update_data["y_pos"]
        
    
    db.commit()
    db.refresh(device)# רענון האובייקט של המכשיר כדי לקבל את הנתונים המעודכנים מהמסד נתונים אחרי העדכון

    # Audit logging
    changes = []
    if old_identifier != device.identifier:
        changes.append(f"identifier: {old_identifier} -> {device.identifier}")
    if old_classification != device.classification:
        changes.append(f"classification: {old_classification} -> {device.classification}")
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

@router.put("/{device_id}/position")# פונקציה לעדכון מיקום המכשיר, מקבלת את ה-ID של המכשיר ואת הקואורדינטות החדשות (x ו-y) בעזרת פרמטרים של השאילתה
def update_device_position(device_id: uuid.UUID, x: float, y: float, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    #find the device
    device = db.query(Device).filter(Device.id == device_id).first()

    #אם המכשיר לא נמצא, נחזיר שגיאה מתאימה
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    

    #check if the user has permission to update the device position (must be admin of the section that the device belongs to)
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have permission to update devices in this section")
    
    #נחפש אם כבר יש רשומה של מיקום למכשיר הזה, אם כן נעדכן אותה, אם לא ניצור רשומה חדשה עם המיקום החדש
    position = db.query(DevicePosition).filter(DevicePosition.device_id == device_id).first()

    #אם אין עדיין רשומה של מיקום למכשיר הזה, ניצור אחת חדשה עם המיקום החדש (או ברירת מחדל אם אחד מהקואורדינטות לא נשלח
    if not position:
        position = DevicePosition(device_id=device_id, x_pos=x, y_pos=y)
        db.add(position)
    else:
        position.x_pos = x
        position.y_pos = y

    db.commit()

    # Audit logging
    LoggerManager.log_audit(
        user=current_user.username,
        action="UPDATE_DEVICE_POSITION",
        target=f"Device:{device.identifier} (ID:{device.id})",
        details=f"New position: x={x}, y={y}"
    )

    return {"status": "success", "device_id": device_id, "new_position": {"x": x, "y": y}}# נחזיר תגובה עם סטטוס ההצלחה, ה-ID של המכשיר והקואורדינטות החדשות שלו


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="You don't have permission to delete devices in this section")
    
    # Audit logging before deletion
    LoggerManager.log_audit(
        user=current_user.username,
        action="DELETE_DEVICE",
        target=f"Device:{device.identifier} (ID:{device.id})",
        details=f"Section ID: {device.section_id}, Classification: {device.classification}"
    )

    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}