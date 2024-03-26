from __future__ import annotations

import datetime
from typing import Sequence, List, Optional, Dict

import discord
import pandas as pd
from discord import app_commands, Guild, Role, SelectOption
from discord.ext import commands

from me.discord_bot.views import me_views

BUTTON_STYLE_ON = discord.ButtonStyle.blurple
BUTTON_STYLE_OFF = discord.ButtonStyle.grey
BUTTON_STYLE_ROLE_BAD = discord.ButtonStyle.red
BUTTON_STYLE_ROLE_GOOD = discord.ButtonStyle.green  # Use BUTTON_STYLE_ON where possible


class MESelect(discord.ui.Select):
    def __init__(self, client: discord.Client, *args, **kwargs):
        self._client = client
        super().__init__(*args, **kwargs)

    async def get_options(self, interaction: discord.Interaction = None):
        return []

    async def initialize(
        self,
        options: Optional[List[SelectOption]] = None,
        interaction: discord.Interaction = None,
    ):
        if options is None:
            options = await self.get_options(interaction)
        if options is not None:
            for option in options:
                self.append_option(option)

    async def callback(self, interaction: discord.Interaction):
        raise NotImplementedError("This is a placeholder")
        # await interaction.response.send_message(
        #     f"TODO big decisions starting here {datetime.datetime.now()}",
        #     view=StaticSampleView(),
        # )


class RoleSelect(MESelect):
    def __init__(self, role_map: Dict[int, str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        for role_id, role_name in role_map.items():
            self.add_option(label=role_name, value=str(role_id))
        self.role_map = role_map

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Awesome! I like {interaction.data['values'][0]} too!",
            view=StaticSampleView(),
        )


class CreateExistingRoleView(me_views.MEView):
    def __init__(self, role_df: pd.DataFrame, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        # self.add_item(me_views.NavButton(linked_view=TodoView(client=self._client), label="Link Role"))

        self.role_df = role_df
        role_map = {
            role_id: role_name for role_id, role_name in self.get_manage_df().values
        }
        if len(role_map) != 0:
            self.add_item(RoleSelect(client=self._client, role_map=role_map))

    def get_manage_df(self):
        df = self.role_df[self.role_df["can_manage"]]
        df = df[df["me_role_id"].isna()]
        return df

    def get_message(self, interaction: discord.Interaction, **kwargs):
        print_df = self.role_df.copy()
        s = ""
        print_df["Can Manage"] = print_df["can_manage"].apply(
            lambda x: "Yes" if x else "No"
        )
        print_df["Linked"] = print_df["me_role_id"].apply(
            lambda x: "Yes" if pd.notna(x) else "No"
        )
        linked_df = self.role_df[self.role_df["me_role_id"].notna()]
        unmanageble_df = self.role_df[~self.role_df["can_manage"]]
        if len(linked_df) > 0:
            s += (
                "Already Linked Roles:\n"
                + ", ".join(linked_df["role_name"].values)
                + "\n"
            )
        if len(unmanageble_df) > 0:
            s += (
                "Role Too Low to Manage:\n"
                + ", ".join(unmanageble_df["role_name"].values)
                + "\n"
            )
        # s = print_df.to_markdown(
        #     tablefmt="ascii",
        #     # headers=["Name", "#", "Price"],
        #     stralign="right",
        #     index=False,
        # )
        if len(self.get_manage_df()) == 0:
            s += "\nNo roles to add"
        return s

    @discord.ui.button(
        label="Add Role",
        style=discord.ButtonStyle.blurple,
        custom_id="me_bot:CreateRoleView:add_role",
    )
    async def add_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            "Replace this with a NavButton",  # TODO
            view=StaticSampleView(),
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.grey,
        custom_id="me_bot:CreateRoleView:back",
    )
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            "Replace this with a back NavButton",  # TODO
            view=StaticSampleView(),
        )


class CreateNewRoleView(me_views.MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        # self.add_item(me_views.NavButton(linked_view=TodoView(client=self._client), label="Add Role"))

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return "Text Box Here"

    @discord.ui.button(
        label="Add Role",
        style=discord.ButtonStyle.blurple,
        custom_id="me_bot:CreateRoleView:add_role",
    )
    async def add_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            "Replace this with a NavButton",
            view=StaticSampleView(),
        )


class CreateExistingRoleButton(me_views.NavButton):
    def __init__(self, **kwargs):
        super().__init__(label="Existing Discord Role", style=BUTTON_STYLE_ON, **kwargs)

    async def get_linked_view(self, interaction: discord.Interaction, **kwargs):
        # TODO filter out @everyone
        user = interaction.user
        can_manage_roles = user.guild_permissions.manage_roles
        top_role = user.top_role.position
        all_roles = [
            (
                role.id,
                role.name,
                can_manage_roles
                and not role.is_default()
                and top_role < user.top_role.position,
            )
            for role in user.guild.roles
        ]
        db_df = self._client.db.get_server_roles_df(interaction.guild_id)
        df = pd.DataFrame(all_roles, columns=["role_id", "role_name", "can_manage"])
        df = df.merge(db_df, how="left", on="role_id")

        return CreateExistingRoleView(client=self._client, role_df=df, **kwargs)


class CreateRoleView(me_views.MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_item(
            me_views.NavButton(
                client=self._client,
                linked_view=CreateNewRoleView(client=self._client),
                label="New Role",
                style=BUTTON_STYLE_ON,
            )
        )
        self.add_item(CreateExistingRoleButton(client=self._client))

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return "Create a new Discord Role?"


class MoreView(me_views.MEView):
    def __init__(self, user=None, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        print("Got view for user", user)
        self.add_item(
            me_views.NavButton(
                linked_view=CreateRoleView(client=self._client),
                label="Add Role",
                style=BUTTON_STYLE_ON,
            )
        )

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return f"Hello {interaction.user.name}, welcome to the More Screen!"


class RoleView(me_views.MEView):
    def __init__(self, ephemeral=False, **kwargs):
        super().__init__(timeout=None, **kwargs)
        self.ephemeral = ephemeral
        self.add_item(
            me_views.NavButton(linked_view=MoreView(client=self._client), label="More")
        )

    def get_message(self, guild: Guild, **kwargs):
        roles: Sequence[Role] = guild.roles
        for role in roles:
            # TODO get roles from database and add role buttons/viws
            pass
        return f"TODO big decisions starting here {datetime.datetime.now()}"

    # @discord.ui.button(
    #     label="More",
    #     style=discord.ButtonStyle.blurple,
    #     custom_id="me_bot:RoleMessageView:more",
    # )
    # async def more(
    #         self, interaction: discord.Interaction, button: discord.ui.Button
    # ):
    #     # noinspection PyUnresolvedReferences
    #     await interaction.response.send_message(
    #         f"TODO Actually put nav bar here {datetime.datetime.now()}",
    #         view=StaticSampleView(),
    #     )

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

    # Select Example (COOL):
    # @discord.ui.select( # the decorator that lets you specify the properties of the select menu
    #     placeholder = "Choose a Flavor!", # the placeholder text that will be displayed if nothing is selected
    #     min_values = 1, # the minimum number of values that must be selected by the users
    #     max_values = 1, # the maximum number of values that can be selected by the users
    #     options = [ # the list of options from which users can choose, a required field
    #         discord.SelectOption(
    #             label="Vanilla",
    #             description="Pick this if you like vanilla!"
    #         ),
    #         discord.SelectOption(
    #             label="Chocolate",
    #             description="Pick this if you like chocolate!"
    #         ),
    #         discord.SelectOption(
    #             label="Strawberry",
    #             description="Pick this if you like strawberry!"
    #         )
    #     ],
    #     custom_id='me_bot:RoleMessageView:SELECT'
    # )
    # async def select_callback(self, interaction, select): # the function called when the user is done selecting options
    #     await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!")


# role_dropdown_group = me_message.MEMessageGroup(
#     me_message.MessageType.PERSONAL_ROLE_MESSAGE, [DropdownView()]
# )


class RoleCommandGroup(app_commands.Group):
    def __init__(self, role_message_group: me_views.MEViewGroup):
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
        print(self.ephemeral)
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
        await interaction.response.send_message(
            f"This is your very own button! ({self.user_id})", ephemeral=True
        )
