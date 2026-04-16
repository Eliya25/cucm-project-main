from sqlalchemy import create_engine  # יצירת engine ל-DB
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # יצירת session  ואופנוע ORM

from app.core.config import settings  # קריאת הגדרות DB

# יצירת מנוע SQLAlchemy מבוסס URL מההגדרות
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

# מאפיין יצירת סשנים
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass  # בסיס למחלקות ORM


# תלות להעברת סשן DB לכל ניתוב עם commit/rollback/close
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # סוגר חיבור
