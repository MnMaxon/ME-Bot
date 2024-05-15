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


def validate_emoji(emoji, default="", raise_error=True):
    if emoji is None:
        return default
    emoji = emoji.strip()
    if emoji == "":
        return default
    err_msg = None
    if " " in emoji or "\t" in emoji:
        err_msg = "Emoji must not contain spaces"
    if len(emoji) < 3:
        err_msg = "Emoji must be at least 2 characters"
    if emoji[0] != ":" or emoji[-1] != ":" or emoji.count(":") != 2:
        err_msg = "Emoji must be in the format :emoji:"
    if err_msg is not None:
        if raise_error:
            raise ValueError("Emoji must be in the format :emoji: not emoji")
        return default
    return emoji
