from typing import Dict

import discord
from typing_extensions import deprecated
import re

from me.discord_bot.views import me_views, nav_ui
from me.discord_bot.views.items import MESelect
from me.discord_bot.views.missing_role_view import MissingRoleView
from me.discord_bot.views.nav_ui import NavSelect
from me.io.data_filter import FilterManager, IsNullFilter

LABEL_SELECT_ROLE = "Select Role"

EMOJI_DEFAULT = ":star:"


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
        if "Discord Role Name" in filtered_keys:
            self.get_view().previous_context["Existing Discord Role"] = False
            context[LABEL_SELECT_ROLE] = None
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


class SelectChannelButton(nav_ui.NavButton):
    def __init__(self, **kwargs):
        super().__init__(
            label="Select Channel",
            linked_view=CreateRoleView,
            style=discord.ButtonStyle.blurple,
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        self.get_view().previous_context["New Channel Name"] = ""
        await super().callback(interaction)


class CancelChannelButton(nav_ui.NavButton):
    def __init__(self, **kwargs):
        super().__init__(
            label="Cancel Channel",
            linked_view=CreateRoleView,
            style=discord.ButtonStyle.grey,
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        self.get_view().previous_context["New Channel Name"] = None
        await super().callback(interaction)


class ChannelSelect(MESelect):
    def __init__(self, channel_map: Dict[int, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        for channel_id, channel_name in channel_map.items():
            self.add_option(label=channel_name, value=str(channel_id))
        self.channel_map = channel_map

    async def callback(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            f"Awesome! I like {interaction.data['values'][0]} too!",
        )


class CreateRoleView(me_views.MEView):
    def __init__(
            self,
            persistent_context=(
                    # "New Role",
                    "Existing Discord Role",
                    "Short Description",
                    "Long Description",
                    "Discord Role Name",
                    "Emoji",
                    LABEL_SELECT_ROLE,
                    LABEL_SELECT_ROLE + "_desc",
                    "Select Channel",
                    "Select Channel_desc",
                    "New Channel Name",
                    "channel_filter",
            ),
            **kwargs,
    ):
        super().__init__(
            timeout=2 * 60, persistent_context=persistent_context, **kwargs
        )
        if self.previous_context.get("channel_filter", None) is None:
            self.previous_context["channel_filter"] = FilterManager(
                filters=[IsNullFilter(col_name="role_id")]
            )

        select_channel = self.previous_context.get("Select Channel", False)

        if select_channel and isinstance(select_channel, bool):
            self.generate_channel_select()
        elif self.previous_context.get("Existing Discord Role", False):
            self.previous_context["Discord Role Name"] = ""
            self.generate_role_select()
        elif self.get_new_role_name() is not None:
            self.add_item(
                nav_ui.NavButton(
                    label="Existing Discord Role",
                    linked_view=CreateRoleView,
                    style=discord.ButtonStyle.grey,
                    row=4
                )
            )
            self.add_item(
                DescriptionModalButton(
                    allow_name=True, style=self.get_edit_emoji_color()
                )
            )
            self.add_channel_buttons()
        else:
            self.add_item(
                DescriptionModalButton(
                    label="New Discord Role",
                    allow_name=True,
                )
            )
            existing_button = nav_ui.NavButton(
                label="Existing Discord Role",
                linked_view=CreateRoleView,
                style=discord.ButtonStyle.blurple
            )
            self.add_item(
                existing_button
            )

        # self.add_nav_button(linked_view=CreateRoleView, label="Refresh", row=4)
        # disable until created
        self.add_nav_button(
            linked_view=CreateRoleView, label="Create", row=4, disabled=True
        )

    def get_channel_df(self):
        channel_df = self.get_client().get_channel_df(
            self.previous_interaction.guild,
            permissions_for=self.previous_interaction.user,
            permission_manage_permissions=True,
        )
        channel_df = self.previous_context["channel_filter"].filter(channel_df)
        return channel_df

    def generate_channel_select(self):
        channel_df = self.get_channel_df()
        channel_df = channel_df[channel_df["manage_permissions"]]
        self.add_item(
            NavSelect(
                options=channel_df[["channel_id", "channel_name"]],
                placeholder="Select Channel",
                context=self.previous_context,
                linked_view=CreateRoleView,
            )
        )

    def add_channel_buttons(self, require_role=True):
        if require_role and self.get_current_role_name() is None:
            return
        if (
                self.get_new_channel_name() is None
                and self.get_existing_channel_id() is None
        ):
            self.add_item(CreateChannelModalButton())
            self.add_item(SelectChannelButton())
        else:
            self.add_item(CancelChannelButton())

    def generate_role_select(self):
        role_map = self.get_role_df()[["role_id", "role_name"]]
        if len(role_map) != 0:
            self.add_item(
                nav_ui.NavSelect(
                    options=role_map,
                    linked_view=CreateRoleView,
                    placeholder=LABEL_SELECT_ROLE,
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
        self.add_item(DescriptionModalButton(style=self.get_edit_emoji_color()))
        self.add_channel_buttons()

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

    def get_edit_emoji_color(self):
        if not self.is_emoji_format_ok() or self.get_emoji() == EMOJI_DEFAULT:
            return discord.ButtonStyle.blurple
        return discord.ButtonStyle.grey

    async def get_context(
            self, interaction: discord.Interaction, clicked_id=None
    ) -> Dict:
        context = await super().get_context(interaction, clicked_id)
        if self.previous_context.get(
                "Existing Discord Role", False
        ):  # Remember if this button is clicked
            context["Existing Discord Role"] = True
        return context

    def get_current_role_name(self):
        if self.get_new_role_name() is not None:
            return self.get_new_role_name()
        return self.get_context_str(
            LABEL_SELECT_ROLE + "_desc",
            self.previous_context.get(LABEL_SELECT_ROLE, None),
        )

    def get_short_description(self):
        return self.get_context_str("Short Description", self.get_current_role_name())

    def get_emoji(self):
        if not self.is_emoji_format_ok():
            return EMOJI_DEFAULT
        return self.get_context_str("Emoji", EMOJI_DEFAULT).strip()

    def is_emoji_format_ok(self):
        emoji = self.get_context_str("Emoji", EMOJI_DEFAULT).strip()
        return emoji.startswith(":") and emoji.endswith(":") and len(emoji) > 2

    def get_message(self, interaction: discord.Interaction, **kwargs):
        role_name = self.get_current_role_name()
        if role_name is not None:
            emoji_warning = ""
            if not self.is_emoji_format_ok():
                emoji_warning = f"    (WARNING: Emoji should be in the format :emoji:  not {self.get_context_str('Emoji', 'emoji')})"
            elif self.get_emoji() == EMOJI_DEFAULT:
                emoji_warning = "    (WARNING: Default Emoji)"
            msg = (
                f"Role:\t\t{role_name}\n"
                f"Button:\t{self.get_emoji()} {self.get_short_description()}{emoji_warning}\n"
            )
            if self.previous_context.get("Long Description", "") != "":
                msg += f"Long Description: {self.previous_context.get('Long Description', '')}\n"
            if self.get_new_channel_name() is not None:
                msg += f"New Channel: {self.get_new_channel_name()}\n"
            elif self.get_existing_channel_name() is not None:
                msg += f"Channel: {self.get_existing_channel_name()}\n"
            # msg += str(self.get_channel_df())
            return msg
        elif self.previous_context.get("Existing Discord Role", False):
            if self.get_role_df().empty:
                msg = "No roles to select from"
            else:
                msg = "Select a Discord Role to create a button for"
        else:
            msg = "Create a new Discord Role?"
        bonus_msg = ""
        if 'bonus_msg' in self.previous_context:
            bonus_msg = "\n\n" + self.previous_context['bonus_msg']
        msg += bonus_msg
        return msg

    def get_role_df(self, require_manage=True, require_missing_me_role=True):
        df = self.get_client().get_role_df(
            self.previous_interaction.guild_id, self.previous_interaction.user
        )
        if require_manage:
            df = df[df["can_manage"]]
        if require_missing_me_role:
            df = df[df["me_role_id"].isna()]
        return df

    def get_existing_channel_id(self):
        channel = self.previous_context.get("Select Channel")
        if channel is not None:
            return int(channel)

    def get_existing_channel_name(self):
        return self.previous_context.get('Select Channel_desc')
