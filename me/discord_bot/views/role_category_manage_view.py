import discord

from me.discord_bot.me_views.me_view import MEView


class RoleCategoryManageView(MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_nav_button(
            linked_view=RoleCategoryManageView,
            label="Add Category",
            style=discord.ButtonStyle.blurple,
        )
        self.add_nav_button(
            linked_view=RoleCategoryManageView,
            label="Manage Categories",
            style=discord.ButtonStyle.grey,
        )

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return ":desktop:  **Role Category Management**"
