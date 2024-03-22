import dataclasses
from enum import Enum
from typing import Dict

from me.io.db_util import SQLiteDB
from permission_types import PermType

@dataclasses.dataclass
class Permission:
    name: str
    # default = None # TODO Get default from discord roles - eg creating channels/roles

@dataclasses.dataclass
class PermissionManager:
    db: SQLiteDB

    def has(self, server_id, user_id, permission: Permission) -> bool:
        df = self.db.get_permission(server_id, user_id, permission.name)
        return len(df) > 0 and df["permission_value"].iloc[0]

    def grant(self, server_id, user_id, permission: Permission or str, value: bool):
        self.db.execute("INSERT INTO permissions (server_id, user_id, permission_id, permission_value) VALUES (?, ?, ?, ?, ?)",
                             (server_id, user_id, permission.id, value))

    def get_all(self, user_id, server_id) -> Dict[PermType, bool]:
        return {p: self.has(user_id, server_id, p) for p in PermType}