from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.models.site import Site, Section

def create_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()

        if existing:
            print("Admin user alredy exists")
            return
        
        admin = User (
            username="admin",
            email="admin@cucm-portal.local",
            hashed_password=hash_password("adminzaq12wsx!!"),
            is_active=True,
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()