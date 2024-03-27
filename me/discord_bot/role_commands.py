from __future__ import annotations

import datetime
from typing import Sequence

import discord
from discord import app_commands, Guild, Role

from me.discord_bot.views import me_views
from me.discord_bot.views.role_add import CreateRoleView


class MoreView(me_views.MEView):
    def __init__(self, user=None, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.add_nav_button(
            linked_view=CreateRoleView,
            label="Add Role",
            style=discord.ButtonStyle.blurple,
        )

    def get_message(self, interaction: discord.Interaction, **kwargs):
        return f"Hello {interaction.user.name}, welcome to the More Screen!"


class RoleView(me_views.MEView):
    def __init__(self, ephemeral=False, **kwargs):
        super().__init__(timeout=None, **kwargs)
        self.ephemeral = ephemeral
        self.add_nav_button(
            linked_view=MoreView(client=self._client),
            label="More",
            replace_message=False,
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
