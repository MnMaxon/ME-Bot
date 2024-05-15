from __future__ import annotations

import datetime

import discord
from discord import app_commands

from me.discord_bot.me_views.me_view import MEView, MEViewGroup
from me.discord_bot.views.admin_view import Admin


class RoleView(MEView):
    def __init__(self, ephemeral=False, **kwargs):
        super().__init__(timeout=None, **kwargs)
        self.ephemeral = ephemeral
        self.add_nav_button(
            linked_view=Admin,
            label="Admin",
            replace_message=False,
        )

    def get_message(
        self, interaction: discord.Interaction | None = None, **kwargs
    ) -> str:
        return (
            f":ballot_box_with_check:  **ME Bot Role Menu**\n"
            f"Bot restarted at {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

    @discord.ui.button(
        label="Change Roles",
        style=discord.ButtonStyle.blurple,
        custom_id="me_bot:RoleMessageView:change_roles",
    )
    async def change_roles(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            f"TODO Actually put stuff here {datetime.datetime.now()}",
            view=StaticSampleView(),
        )


class RoleCommandGroup(app_commands.Group):
    def __init__(self, role_message_group: MEViewGroup):
        super().__init__(name="role", description="Commands for managing roles")
        self.client = role_message_group.get_client()
        self.message_group = role_message_group
        # more_view.register(self.client)
        # role_dropdown_group.register(self.client)
        # For dynamic items, we must register the classes instead of the views.
        # self.client.add_dynamic_items(DynamicButton)

    @app_commands.command()
    async def message(self, interaction: discord.Interaction):
        await self.message_group.display(interaction=interaction)


class StaticSampleView(discord.ui.View):
    def __init__(self, ephemeral=True):
        super().__init__(timeout=None)
        self.ephemeral = ephemeral

    @discord.ui.button(
        label="Blurple",
        style=discord.ButtonStyle.blurple,
        custom_id="me_bot:MessageDropdown:todo43134",
    )
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            "This is blurple.", ephemeral=self.ephemeral
        )


class DynamicButton(discord.ui.Button):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            # discord.ui.Button(
            label="Do Thing",
            style=discord.ButtonStyle.blurple,
            custom_id=f"button:user:{user_id}",
            emoji="\N{THUMBS UP SIGN}",
            # )
        )
        self.user_id: int = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            f"This is your very own button! ({self.user_id})", ephemeral=True
        )
