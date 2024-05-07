from pathlib import Path
from typing import Union

import discord


def get_data_folder():
    return Path("data")


def can_manage(user: Union[discord.User, discord.Member], role: discord.Role):
    return (
        user.guild_permissions.manage_roles
        and not role.is_default()
        and (user.guild.owner_id == user.id or role.position < user.top_role.position)
    )
