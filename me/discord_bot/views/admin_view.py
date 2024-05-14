from __future__ import annotations

import discord

from me.discord_bot.views.me_views import MEView
from me.discord_bot.views.role_add import CreateRoleView


class Admin(MEView):
    def __init__(self, user=None, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_nav_button(
            linked_view=CreateRoleView,
            label="Add Role",
            style=discord.ButtonStyle.blurple,
        )

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return f"Hello {interaction.user.name}, welcome to the More Screen!"
