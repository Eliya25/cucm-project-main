import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session, joinedload
import openpyxl
import io

from app.db.session import get_db
from app.models.device import DevicePosition, Device
from app.models.roles import UserRole
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.core.dependencies import get_current_user, require_operator
from app.models.user import User
from logger_manager import LoggerManager

router = APIRouter()


def is_valid_mac(mac: str) -> bool:
    """בודק אם המחרוזת היא כתובת MAC תקינה"""
    mac = mac.strip()
    pattern = r'^([0-9A-Fa-f]{2}[:\-\.]){5}([0-9A-Fa-f]{2})$'
    return bool(re.match(pattern, mac))


def normalize_mac(mac: str) -> str:
    """ממיר כתובת MAC לפורמט אחיד עם נקודותיים"""
    mac = mac.strip().upper()
    # מסיר מפרידים ומוסיף נקודותיים
    digits = re.sub(r'[:\-\.]', '', mac)
    return ':'.join(digits[i:i+2] for i in range(0, 12, 2))


# ══════════════════════════════════════════════════════
#  IMPORT FROM EXCEL
# ══════════════════════════════════════════════════════

@router.post("/import/{section_id}")
async def import_devices_from_excel(
    section_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """
    מייבא כתובות MAC מקובץ Excel לתא מסוים.
    - קורא כל עמודה בכל שורה ומחפש כתובות MAC תקינות
    - מדלג על כתובות שכבר קיימות במערכת
    - מחזיר סיכום: כמה נוספו, כמה כפולות, כמה לא תקינות
    """
    # בדיקת הרשאות
    if not current_user.is_admin_of_section(section_id):
        raise HTTPException(
            status_code=403,
            detail="No admin permission for this section"
        )

    # בדיקת סוג קובץ
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx, .xls) are supported"
        )

    # קריאת הקובץ
    try:
        contents = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        ws = wb.active
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read Excel file")

    # איסוף כל כתובות ה-MAC מהקובץ
    found_macs = []
    invalid_count = 0

    for row in ws.iter_rows(values_only=True):
        for cell in row:
            if cell is None:
                continue
            value = str(cell).strip()
            if not value:
                continue

            if is_valid_mac(value):
                found_macs.append(normalize_mac(value))
            else:
                # תא לא ריק אבל לא MAC תקין — מונים אותו
                if value and value != 'None':
                    invalid_count += 1

    if not found_macs:
        raise HTTPException(
            status_code=400,
            detail="No valid MAC addresses found in the file"
        )

    # הסרת כפולות בתוך הקובץ עצמו
    unique_macs = list(dict.fromkeys(found_macs))
    duplicates_in_file = len(found_macs) - len(unique_macs)

    # בדיקה מה כבר קיים ב-DB
    existing = db.query(Device).filter(
        Device.identifier.in_(unique_macs)
    ).all()
    existing_macs = {d.identifier for d in existing}

    # יצירת devices חדשים בלבד
    new_macs = [mac for mac in unique_macs if mac not in existing_macs]
    already_exists_count = len(existing_macs)

    created = []
    for mac in new_macs:
        device = Device(identifier=mac, section_id=section_id)
        db.add(device)
        db.flush()
        db.add(DevicePosition(device_id=device.id, x_pos=0.0, y_pos=0.0))
        created.append(mac)

    db.commit()

    LoggerManager.log_audit(
        user=current_user.username,
        action="IMPORT_DEVICES_FROM_EXCEL",
        target=f"Section:{section_id}",
        details=f"Added: {len(created)}, Already exists: {already_exists_count}, Invalid: {invalid_count}"
    )

    return {
        "success": True,
        "summary": {
            "total_in_file":     len(found_macs),
            "added":             len(created),
            "already_exists":    already_exists_count,
            "duplicates_in_file": duplicates_in_file,
            "invalid_cells":     invalid_count,
        },
        "added_macs": created
    }


# ══════════════════════════════════════════════════════
#  STANDARD CRUD
# ══════════════════════════════════════════════════════

@router.get("/", response_model=list[DeviceResponse])
def get_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Device).options(joinedload(Device.section))

    if current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return query.all()

    allowed_section_ids = list(current_user.allowed_section_ids)
    if not allowed_section_ids:
        return []

    return query.filter(Device.section_id.in_(allowed_section_ids)).all()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if not current_user.has_section_access(device.section_id):
        raise HTTPException(status_code=403, detail="Access denied")

    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(device_data: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):
    if not current_user.is_admin_of_section(device_data.section_id):
        raise HTTPException(status_code=403, detail="No admin permission for this section")

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
        user=current_user.username, action="CREATE_DEVICE",
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
        raise HTTPException(status_code=403, detail="No admin permission for this section")

    update_data = device_data.model_dump(exclude_unset=True)
    old_identifier = device.identifier

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

    if old_identifier != device.identifier:
        LoggerManager.log_audit(
            user=current_user.username, action="UPDATE_DEVICE",
            target=f"Device:{device.identifier} (ID:{device.id})",
            details=f"identifier: {old_identifier} → {device.identifier}"
        )
    return device


@router.put("/{device_id}/position")
def update_device_position(device_id: uuid.UUID, x: float, y: float, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="No admin permission")

    position = db.query(DevicePosition).filter(DevicePosition.device_id == device_id).first()

    if not position:
        position = DevicePosition(device_id=device_id, x_pos=x, y_pos=y)
        db.add(position)
    else:
        position.x_pos = x
        position.y_pos = y

    db.commit()
    return {"status": "success", "new_position": {"x": x, "y": y}}


@router.delete("/{device_id}", status_code=status.HTTP_200_OK)
def delete_device(device_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_operator)):

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if not current_user.is_admin_of_section(device.section_id):
        raise HTTPException(status_code=403, detail="No admin permission")

    identifier = device.identifier

    LoggerManager.log_audit(
        user=current_user.username, action="DELETE_DEVICE",
        target=f"Device:{identifier} (ID:{device_id})",
        details=f"Section ID: {device.section_id}"
    )

    db.delete(device)
    db.commit()

    return {"message": f"Device '{identifier}' deleted successfully"}