from typing import Dict

import discord
import pandas as pd
from typing_extensions import deprecated

from me.discord_bot.views import me_views, nav_ui
from me.discord_bot.views.items import MESelect


@deprecated
class RoleSelect(MESelect):
    def __init__(self, role_map: Dict[int, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        for role_id, role_name in role_map.items():
            self.add_option(label=role_name, value=str(role_id))
        self.role_map = role_map

    async def callback(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            f"Awesome! I like {interaction.data['values'][0]} too!",
        )


class MissingRoleView(me_views.MEView):
    def __init__(self, role_df: pd.DataFrame = None, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.role_df = role_df

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


class CreateExistingRoleButton(nav_ui.NavButton):
    def __init__(self, **kwargs):
        super().__init__(
            label="Existing Discord Role",
            linked_view=CreateRoleView,
            style=discord.ButtonStyle.blurple,
            **kwargs,
        )

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        context = await super().get_context(interaction, clicked_id)
        user = interaction.user
        can_manage_roles = user.guild_permissions.manage_roles
        top_role = user.top_role.position
        all_roles = [
            (
                role.id,
                role.name,
                can_manage_roles
                and not role.is_default()
                and (
                    user.guild.owner_id == user.id or top_role < user.top_role.position
                ),
            )
            for role in user.guild.roles
        ]
        db_df = self.get_client().db.get_server_roles_df(interaction.guild_id)
        df = pd.DataFrame(all_roles, columns=["role_id", "role_name", "can_manage"])
        df = df.merge(db_df, how="left", on="role_id")
        context["role_df"] = df
        return context


class CreateRoleView(me_views.MEView):
    def __init__(
        self,
        persistent_context=("role_df", "New Role", "Existing Discord Role"),
        **kwargs,
    ):
        super().__init__(
            timeout=2 * 60, persistent_context=persistent_context, **kwargs
        )
        if self.previous_context.get("Existing Discord Role", False):
            role_map = {
                role_id: role_name
                for role_id, role_name in self.get_manage_df()
                .sort_values("role_name")[["role_id", "role_name"]]
                .values
            }
            if len(role_map) != 0:
                self.add_item(
                    nav_ui.NavSelect(
                        options=role_map,
                        linked_view=CreateRoleView,
                        placeholder="Select Role",
                        context=self.previous_context,
                    )
                )
        elif self.previous_context.get("New Role", False):
            # TODO Text Input cannot be added to views - Needs to be added through the message or something
            # self.add_item(discord.ui.TextInput(label="New Role Name", row=1))
            pass
        else:
            self.add_nav_button(
                linked_view=CreateRoleView,
                label="New Role",
                style=discord.ButtonStyle.blurple,
            )
            self.add_item(CreateExistingRoleButton())
        self.add_nav_button(linked_view=CreateRoleView, label="Create", row=4)
        self.add_nav_button(linked_view=CreateRoleView, label="Refresh", row=4)

    async def get_context(
        self, interaction: discord.Interaction, clicked_id=None
    ) -> Dict:
        context = await super().get_context(interaction, clicked_id)
        if self.previous_context.get(
            "Existing Discord Role", False
        ):  # Remember if this button is clicked
            context["Existing Discord Role"] = True
        return context

    def get_manage_df(self) -> pd.DataFrame:
        df = self.get_role_df()
        df = df[df["can_manage"]]
        df = df[df["me_role_id"].isna()]
        return df

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return "Create a new Discord Role?"

    def get_role_df(self):
        return self.previous_context.get("role_df")
