from app.db.session import SessionLocal
from app.models.user import User
from app.models.roles import UserRole
from app.core.security import hash_password
from app.models.site import Site, Section
from app.models.group import Group, UserGroup, SectionGroup
from app.models.device import Device, DevicePosition

def create_super_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "superadmin").first()

        if existing:
            print("Super admin user already exists")
            return
        
        super_admin = User (
            username="superadmin",
            hashed_password=hash_password("superadminzaq12wsx!!"),
            is_active=True,
            role=UserRole.SUPERADMIN
        )
        db.add(super_admin)
        db.commit()
        print("Super admin user created successfully")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()