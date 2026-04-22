from enum import Enum

class UserRole(str, Enum):

    """
    היררכיית הרשאות:
    SUPERADMIN  → שולט על הכל, יוצר Admins, מוחק Sites/Sections
    ADMIN       → מנהל אתרים, תאים, יוצר Operators/Viewers, מנהל Groups
    OPERATOR    → יכול להוסיף/לערוך Devices בתאים שלו
    VIEWER      → צופה בלבד
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
