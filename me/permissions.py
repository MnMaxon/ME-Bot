import dataclasses
from enum import Enum
from typing import Dict


@dataclasses.dataclass
class Permission:
    name: str
    # default = None # TODO Get default from discord roles - eg creating channels/roles


PERM_CHANNELS_VIEW = Permission('channels.view')
PERM_CHANNELS_CREATE = Permission('channels.view')
PERM_ROLES_VIEW = Permission('roles.view')
PERM_ROLES_CREATE = Permission('roles.create')

_all_permissions: dict[str, Permission] = {
    p.name: p for p in [PERM_CHANNELS_VIEW,
                        PERM_CHANNELS_CREATE,
                        PERM_ROLES_VIEW,
                        PERM_ROLES_CREATE, ]
}


@dataclasses.dataclass
class PermissionManager:
    def has(self, user_id, server_id, permission: Permission or str) -> bool:
        permission = self.get_permission(permission)

    def get_all(self, user_id, server_id) -> Dict[str, bool]:
        return {p: self.has(user_id, server_id, p) for p in _all_permissions.keys()}

    def get_permission(self, permission: str or Permission):
        if isinstance(permission, Permission):
            permission = permission.name
        if permission not in _all_permissions:
            raise ValueError(f"Permission {permission} not in {_all_permissions.keys()}")
        return _all_permissions[permission]
