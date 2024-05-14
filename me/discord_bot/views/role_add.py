import math
import pprint
from typing import Dict

import discord
from typing_extensions import deprecated
import re

from me.discord_bot.views import me_views, nav_ui
from me.discord_bot.views.items import MESelect
from me.discord_bot.views.missing_role_view import MissingRoleView
from me.discord_bot.views.nav_ui import NavSelect
from me.io.data_filter import FilterManager, IsNullFilter

EXISTING_DISCORD_ROLE = "Existing Discord Role"
NEW_CHANNEL_NAME = "New Channel Name"
LONG_DESCRIPTION = "Long Description"
SHORT_DESCRIPTION = "Short Description"
DISCORD_ROLE_NAME = "Discord Role Name"
SELECT_CHANNEL = "Select Channel"
SELECT_CHANNEL_DESC = "Select Channel_desc"
SELECT_ROLE = "Select Role"
EMOJI_DEFAULT = ":star:"
EMOJI_OCTAGONAL=':octagonal_sign:'


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
        label=DISCORD_ROLE_NAME,
        placeholder="New role name here",
        max_length=100,
        required=True,
    )
    emoji = discord.ui.TextInput(
        label="Emoji",
        placeholder="Paste emoji here, can edit later (:star:)",
        required=False,
    )
    short_description = discord.ui.TextInput(
        label=SHORT_DESCRIPTION,
        placeholder="(Default: role name) Name on button",
        required=False,
        max_length=100,
    )
    long_description = discord.ui.TextInput(
        label=LONG_DESCRIPTION,
        placeholder="Doesn't really do anything yet",
        required=False,
        max_length=400,
    )


class NewChannelModal(nav_ui.NavModal, title="New Channel"):
    discord_role_name = discord.ui.TextInput(
        label=NEW_CHANNEL_NAME,
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
            allow_list.append(DISCORD_ROLE_NAME)
        if allow_emoji:
            label_list.append("Emoji")
            allow_list.append("Emoji")
        if allow_descriptions:
            label_list.append("Descriptions")
            allow_list.append(SHORT_DESCRIPTION)
            allow_list.append(LONG_DESCRIPTION)
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
        if DISCORD_ROLE_NAME in filtered_keys:
            self.get_view().previous_context[EXISTING_DISCORD_ROLE] = False
            context[SELECT_ROLE] = None
            context[EXISTING_DISCORD_ROLE] = False
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
            label=SELECT_CHANNEL,
            linked_view=CreateRoleView,
            style=discord.ButtonStyle.blurple,
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        self.get_view().previous_context[NEW_CHANNEL_NAME] = ""
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
        self.get_view().previous_context[NEW_CHANNEL_NAME] = None
        self.get_view().previous_context[SELECT_CHANNEL] = None
        self.get_view().previous_context[SELECT_CHANNEL_DESC] = None
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
            EXISTING_DISCORD_ROLE,
            SHORT_DESCRIPTION,
            LONG_DESCRIPTION,
            DISCORD_ROLE_NAME,
            "Emoji",
            SELECT_ROLE,
            SELECT_ROLE + "_desc",
            SELECT_CHANNEL,
            SELECT_CHANNEL_DESC,
            NEW_CHANNEL_NAME,
            "channel_filter",
        ),
        **kwargs,
    ):
        super().__init__(
            timeout=2 * 60, persistent_context=persistent_context, **kwargs
        )
        new_role_name = self.get_new_role_name()
        if new_role_name is not None and new_role_name in [
            role.name for role in self.previous_interaction.guild.roles
        ]:
            del self.previous_context[DISCORD_ROLE_NAME]
            msg = f"{EMOJI_OCTAGONAL}  The role '{new_role_name}' already exists, please select a different name"
            self.previous_context["bonus_msg"] = msg
        new_channel_name = self.get_new_channel_name()
        if new_channel_name is not None and new_channel_name in [
            channel.name for channel in self.previous_interaction.guild.channels
        ]:
            del self.previous_context[NEW_CHANNEL_NAME]
            msg = f"{EMOJI_OCTAGONAL}  The channel '{new_channel_name}' already exists, please select a different name"
            self.previous_context["bonus_msg"] = msg
        if self.previous_context.get("channel_filter", None) is None:
            self.previous_context["channel_filter"] = FilterManager(
                filters=[IsNullFilter(col_name="role_id")]
            )

        select_channel = self.previous_context.get(SELECT_CHANNEL, False)

        if select_channel and isinstance(select_channel, bool):
            self.generate_channel_select()
        elif self.previous_context.get(EXISTING_DISCORD_ROLE, False):
            self.previous_context[DISCORD_ROLE_NAME] = ""
            self.generate_role_select()
        elif self.get_new_role_name() is not None:
            self.add_item(
                nav_ui.NavButton(
                    label=EXISTING_DISCORD_ROLE,
                    linked_view=CreateRoleView,
                    style=discord.ButtonStyle.grey,
                    row=4,
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
                label=EXISTING_DISCORD_ROLE,
                linked_view=CreateRoleView,
                style=discord.ButtonStyle.blurple,
            )
            self.add_item(existing_button)

        # self.add_nav_button(linked_view=CreateRoleView, label="Refresh", row=4)
        # disable until created
        self.add_nav_button(
            linked_view=CreateRoleView, label="Create", row=4, disabled=self.get_current_role_name() is None
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
                placeholder=SELECT_CHANNEL,
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
                    placeholder=SELECT_ROLE,
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
        return self.get_context_str(DISCORD_ROLE_NAME, None)

    def get_new_channel_name(self):
        name = self.get_context_str(NEW_CHANNEL_NAME, "")
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
            EXISTING_DISCORD_ROLE, False
        ):  # Remember if this button is clicked
            context[EXISTING_DISCORD_ROLE] = True
        return context

    def get_current_role_name(self):
        if self.get_new_role_name() is not None:
            return self.get_new_role_name()
        return self.get_context_str(
            SELECT_ROLE + "_desc",
            self.previous_context.get(SELECT_ROLE, None),
        )

    def get_short_description(self):
        return self.get_context_str(SHORT_DESCRIPTION, self.get_current_role_name())

    def get_emoji(self):
        if not self.is_emoji_format_ok():
            return EMOJI_DEFAULT
        return self.get_context_str("Emoji", EMOJI_DEFAULT).strip()

    def is_emoji_format_ok(self):
        emoji = self.get_context_str("Emoji", EMOJI_DEFAULT).strip()
        return emoji.startswith(":") and emoji.endswith(":") and len(emoji) > 2

    def get_message(self, interaction: discord.Interaction or None = None, **kwargs):
        role_name = self.get_current_role_name()
        if role_name is not None:
            msg = self.get_message_overview()
        elif self.previous_context.get(EXISTING_DISCORD_ROLE, False):
            if self.get_role_df().empty:
                msg = "No roles to select from"
            else:
                msg = "Select a Discord Role to create a button for"
        else:
            msg = "Create a new Discord Role?"
        bonus_msg = ""
        if "bonus_msg" in self.previous_context:
            bonus_msg = "\n\n" + self.previous_context["bonus_msg"]
        msg += bonus_msg
        return msg

    def get_message_overview(self):
        warnings = []
        info = {}
        role = self.get_current_role_name()
        if not self.is_emoji_format_ok():
            em = self.get_context_str("Emoji", "emoji")
            warnings.append(f"Emoji should be in the format :emoji: not {em}")
        if self.get_emoji() == EMOJI_DEFAULT:
            warnings.append(f"You are using the default emoji ({EMOJI_DEFAULT})")
        info['Role'] = role
        info['Button'] = f"{self.get_emoji()} {self.get_short_description()}"
        desc = self.previous_context.get(LONG_DESCRIPTION, "")
        if desc != "":
            info['Desc'] = desc
        if self.get_new_channel_name() is not None:
            info['Channel'] = self.get_new_channel_name()
        elif self.get_existing_channel_name() is not None:
            info['Channel'] = self.get_existing_channel_name()
        else:
            warnings.append(f"No channel selected - {role} will not be linked to any new channels")

        msg = ""
        tab_len = 4
        longest = max(len(k) for k in info.keys())
        base_tabs = math.ceil(longest/tab_len) + 1
        for k, v in info.items():
            tabs = "\t" * (base_tabs - math.ceil(len(k)/tab_len))
            msg += f"**{k}:**{tabs}{v}\n"

        if len(warnings) > 0:
            msg += "\n:warning:  **WARNINGS**  :warning:\n" + "\n".join(warnings)
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
        channel = self.previous_context.get(SELECT_CHANNEL)
        if channel is not None:
            return int(channel)

    def get_existing_channel_name(self):
        return self.previous_context.get(SELECT_CHANNEL_DESC)
