from typing import Dict

import discord
import pandas as pd
from typing_extensions import deprecated
import re

from me.discord_bot.views import me_views, nav_ui
from me.discord_bot.views.items import MESelect
from me.discord_bot.views.missing_role_view import MissingRoleView


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


class CreateExistingRoleButton(nav_ui.NavButton):
    def __init__(self, **kwargs):
        if "style" not in kwargs:
            kwargs["style"] = discord.ButtonStyle.blurple
        super().__init__(
            label="Existing Discord Role",
            linked_view=CreateRoleView,
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

    async def callback(self, interaction: discord.Interaction):
        self.get_view().previous_context["Discord Role Name"] = ""
        await super().callback(interaction)


class DescriptionModal(nav_ui.NavModal, title="Optional Descriptions"):
    discord_role_name = discord.ui.TextInput(
        label="Discord Role Name",
        placeholder="New role name here",
        max_length=100,
        required=True,
    )
    short_description = discord.ui.TextInput(
        label="Short Description",
        placeholder="(Default: role name) Name on button",
        required=False,
        max_length=100,
    )
    long_description = discord.ui.TextInput(
        label="Long Description",
        placeholder="Doesn't really do anything yet",
        required=False,
        max_length=400,
    )
    emoji = discord.ui.TextInput(
        label="Emoji",
        placeholder="Paste emoji here, can edit later (:star:)",
        required=False,
    )


class NewChannelModal(nav_ui.NavModal, title="New Channel"):
    discord_role_name = discord.ui.TextInput(
        label="New Channel Name",
        placeholder="New role name here",
        max_length=100,
        required=True,
    )


# class NewRoleModal(DescriptionModal, title='New Role'):


class DescriptionModalButton(nav_ui.ModalButton):
    def __init__(
        self, allow_name=False, allow_emoji=True, allow_descriptions=True, **kwargs
    ):
        modal = DescriptionModal(self)
        label_list = []
        allow_list = []
        if allow_name:
            label_list.append("Role")
            allow_list.append("Discord Role Name")
        if allow_emoji:
            label_list.append("Emoji")
            allow_list.append("Emoji")
        if allow_descriptions:
            label_list.append("Descriptions")
            allow_list.append("Short Description")
            allow_list.append("Long Description")
        kwargs["label"] = kwargs.get("label", "Edit " + "/".join(label_list))
        kwargs["style"] = kwargs.get("style", discord.ButtonStyle.blurple)
        super().__init__(
            modal=modal,
            linked_view=CreateRoleView,
            allowed_text_inputs=allow_list,
            **kwargs,
        )

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        # Deletes selected role if it exists
        context = await super().get_context(interaction, clicked_id)
        filtered_keys = [k for k, v in context.items() if v is not None and v != ""]
        print("VALUES", filtered_keys)
        if "Discord Role Name" in filtered_keys:
            self.get_view().previous_context["Existing Discord Role"] = False
            context["Select Role"] = None
            context["Existing Discord Role"] = False
        return context


class CreateChannelModalButton(nav_ui.ModalButton):
    def __init__(
        self, style=discord.ButtonStyle.blurple, label="New Channel", **kwargs
    ):
        modal = NewChannelModal(self)
        super().__init__(
            modal=modal,
            linked_view=CreateRoleView,
            style=style,
            label=label,
            **kwargs,
        )


class CreateRoleView(me_views.MEView):
    def __init__(
        self,
        persistent_context=(
            "role_df",
            # "New Role",
            "Existing Discord Role",
            "Short Description",
            "Long Description",
            "Discord Role Name",
            "Emoji",
            "Select Role",
            "Select Role Desc",
            "New Channel Name",
        ),
        **kwargs,
    ):
        super().__init__(
            timeout=2 * 60, persistent_context=persistent_context, **kwargs
        )
        # print("previous context", self.previous_context)
        if self.previous_context.get("Existing Discord Role", False):
            self.generate_role_select()
        elif self.get_new_role_name() is not None:
            self.add_item(
                CreateExistingRoleButton(style=discord.ButtonStyle.grey, row=4)
            )
            self.add_item(DescriptionModalButton(allow_name=True))
            self.add_item(CreateChannelModalButton())
        else:
            self.add_item(
                DescriptionModalButton(
                    label="New Discord Role",
                    allow_name=True,
                )
            )
            self.add_item(CreateExistingRoleButton())

        self.add_nav_button(linked_view=CreateRoleView, label="Refresh", row=4)
        # disable until created
        self.add_nav_button(
            linked_view=CreateRoleView, label="Create", row=4, disabled=True
        )

    def generate_role_select(self):
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
        self.add_nav_button(linked_view=MissingRoleView, label="Missing Roles?", row=4)
        # self.add_nav_button(linked_view=MissingRoleView, label="Next", style=discord.ButtonStyle.blurple,row=4)
        self.add_item(
            DescriptionModalButton(
                label="New Discord Role",
                allow_name=True,
                style=discord.ButtonStyle.grey,
                row=4,
            )
        )
        self.add_item(DescriptionModalButton())

    def get_context_str(self, key, default=None):
        val = self.previous_context.get(key, default)
        if val is None or val == "" or val == "None":
            return default
        return val

    def get_new_role_name(self):
        return self.get_context_str("Discord Role Name", None)

    def get_new_channel_name(self):
        name = self.get_context_str("New Channel Name", "")
        if name is not None:
            name = name.replace(" ", "-").lower()
            name = re.sub(r"[^a-zA-Z0-9_\-]", "", name)
        if name == "":
            return None
        return name

    def get_current_channel_name(self):
        channel_name = self.get_new_channel_name()
        return channel_name

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

    def get_current_role_name(self):
        if self.get_new_role_name() is not None:
            return self.get_new_role_name()
        if self.previous_context.get("Select Role", None) is not None:
            return self.get_context_str(
                "Select Role Desc", self.previous_context.get("Select Role", None)
            )

    def get_short_description(self):
        return self.get_context_str("Short Description", self.get_current_role_name())

    def get_emoji(self):
        star = ":star:"
        if not self.is_emoji_format_ok():
            return star
        return self.get_context_str("Emoji", star).strip()

    def is_emoji_format_ok(self):
        emoji = self.get_context_str("Emoji", ":star:").strip()
        return emoji.startswith(":") and emoji.endswith(":") and len(emoji) > 2

    def get_message(self, interaction: discord.Interaction, **kwargs):
        role_name = self.get_current_role_name()
        if role_name is not None:
            emoji_warning = ""
            if not self.is_emoji_format_ok():
                emoji_warning = f" <- (WARNING: Emoji should be in the format :emoji:  not {self.get_context_str('Emoji', 'emoji')})"
            elif self.get_emoji() == ":star:":
                emoji_warning = " <- (WARNING: Default Emoji)"
            return (
                f"Discord Role: {role_name}\n"
                f"Short Description: {self.get_short_description()}\n"
                f"Long Description: {self.previous_context.get('Long Description', '')}\n"
                f"Emoji: {self.get_emoji()}{emoji_warning}\n"
                f"Channel: {self.get_current_channel_name()}"
            )
        return "Create a new Discord Role?"

    def get_role_df(self):
        return self.previous_context.get("role_df")
