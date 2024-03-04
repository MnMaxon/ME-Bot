import dataclasses
from enum import Enum


_all_permissions = []

@dataclasses.dataclass
class Permission:
    permission_name: str
@dataclasses.dataclass
class PermissionManager:
    pass