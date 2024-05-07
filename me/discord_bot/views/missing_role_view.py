import discord
from me.discord_bot.views import me_views


class MissingRoleView(me_views.MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_back_button()

    def get_message(self, interaction: discord.Interaction = None, **kwargs):
        df = self.get_client().get_role_df(
            self.previous_interaction.guild_id, self.previous_interaction.user
        )
        s = ""
        linked_df = df[df["me_role_id"].notna()]
        if len(linked_df) > 0:
            s += (
                "Already Linked Roles:\n"
                + " - ".join(linked_df["role_name"].values)
                + "\n\n"
            )
        manage_false_df = df[~df["can_manage"]]
        if len(manage_false_df) > 0:
            s += (
                "Role Too Low to Manage:\n"
                + " - ".join(manage_false_df["role_name"].values)
                + "\n\n"
            )
        return s
