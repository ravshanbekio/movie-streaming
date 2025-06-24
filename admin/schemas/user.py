from enum import Enum

class AdminRole(str, Enum):
    owner = "owner"
    admin = "admin"