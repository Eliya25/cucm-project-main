from enum import Enum

class UserRole(Enum):
    SUPERADMIN = "superadmin"
    OPERATOR = "operator"
    VIEWER = "viewer"
