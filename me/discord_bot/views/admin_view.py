from __future__ import annotations

import discord

from me.discord_bot.me_views.me_view import MEView
from me.discord_bot.views.role_add import CreateRoleView
from me.discord_bot.views.role_category_add_view import (
    RoleCategoryAddView,
)
from me.discord_bot.views.role_category_manage_view import RoleCategoryManageView


class Admin(MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_nav_button(
            linked_view=CreateRoleView,
            label="Add Role",
            style=discord.ButtonStyle.blurple,
        )
        self.add_nav_button(
            linked_view=CreateRoleView,
            label="TODO: Manage Roles",  # TODO
            style=discord.ButtonStyle.grey,
        )
        self.add_nav_button(
            linked_view=CreateRoleView,
            label="TODO: Hide Roles",  # TODO
            style=discord.ButtonStyle.grey,
        )
        self.add_nav_button(
            linked_view=RoleCategoryAddView,
            label="Create Category",
            style=discord.ButtonStyle.grey,
            row=1,
        )
        self.add_nav_button(
            linked_view=RoleCategoryManageView,
            label="TODO: Manage Categories",  # TODO
            style=discord.ButtonStyle.grey,
            row=1,
        )

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return ":desktop:  **Admin Menu**"
