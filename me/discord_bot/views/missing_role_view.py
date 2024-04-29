import discord
import pandas as pd

from me.discord_bot.views import me_views


class MissingRoleView(me_views.MEView):
    def __init__(self, role_df: pd.DataFrame = None, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.role_df = role_df
        self.add_back_button()
        if self.role_df is None:
            self.role_df = self.previous_context.get("role_df")

    def get_message(self, interaction: discord.Interaction, **kwargs):
        s = ""
        linked_df = self.role_df[self.role_df["me_role_id"].notna()]
        if len(linked_df) > 0:
            s += (
                "Already Linked Roles:\n"
                + " - ".join(linked_df["role_name"].values)
                + "\n\n"
            )
        manage_false_df = self.role_df[~self.role_df["can_manage"]]
        if len(manage_false_df) > 0:
            s += (
                "Role Too Low to Manage:\n"
                + " - ".join(manage_false_df["role_name"].values)
                + "\n\n"
            )
        # s = print_df.to_markdown(
        #     tablefmt="ascii",
        #     # headers=["Name", "#", "Price"],
        #     stralign="right",
        #     index=False,
        # )
        return s
