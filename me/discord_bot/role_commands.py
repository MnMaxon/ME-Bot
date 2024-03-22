from __future__ import annotations

import datetime

import discord
from discord import app_commands
from discord.ext import commands

from me.discord_bot.views import me_message

BUTTON_STYLE_ON = discord.ButtonStyle.blurple
BUTTON_STYLE_OFF = discord.ButtonStyle.grey
BUTTON_STYLE_ROLE_BAD = discord.ButtonStyle.red
BUTTON_STYLE_ROLE_GOOD = discord.ButtonStyle.green  # Use BUTTON_STYLE_ON where possible


class RoleMessage(me_message.MEMessage):
    def get_message(self):
        return f"TODO big decisions starting here {datetime.datetime.now()}"

    def get_view(self) -> discord.ui.View:
        return RoleMessageView()


class DropdownMessage(me_message.MEMessage):
    def get_message(self):
        return f"Dropdown message! {datetime.datetime.now()}"

    def get_view(self) -> discord.ui.View:
        return MessageDropdownView()


role_group = me_message.MEMessageGroup(me_message.MessageType.ROLE_MESSAGE, [RoleMessage()], max_messages_per_channel=1)
dropdown_group = me_message.MEMessageGroup(me_message.MessageType.PERSONAL_ROLE_MESSAGE, [DropdownMessage()])


class RoleGroup(app_commands.Group):
    def __init__(self, client: discord.Client):
        super().__init__(name="role", description="Commands for managing roles")
        self.client = client
        role_group.register(self.client)
        dropdown_group.register(self.client)
        # For dynamic items, we must register the classes instead of the views.
        # self.client.add_dynamic_items(DynamicButton)

    @app_commands.command()
    async def message(self, interaction: discord.Interaction):
        await role_group.display(channel=interaction.channel_id, interaction=interaction)

    @app_commands.command(
        description="Sample Persistent view from github")
    @commands.is_owner()
    async def sample(self, interaction: discord.Interaction):
        """Starts a persistent view."""
        # In order for a persistent view to be listened to, it needs to be sent to an actual message.
        # Call this method once just to store it somewhere.
        # In a more complicated program you might fetch the message_id from a database for use later.
        # However, this is outside the scope of this simple example.
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message("What's your favourite colour?", view=PersistentView())

    @app_commands.command(
        description="Sample Dynamic view from github")
    @commands.is_owner()
    async def sample2(self, interaction: discord.Interaction):
        """Starts a dynamic button."""

        view = discord.ui.View(timeout=None)
        view.add_item(DynamicButton(interaction.user.id))
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message('Here is your very own button!', view=view)


class RoleMessageView(discord.ui.View):
    def __init__(self, ephemeral=False):
        super().__init__(timeout=None)
        self.ephemeral = ephemeral

    @discord.ui.button(label='Change Roles', style=discord.ButtonStyle.blurple, custom_id='me_bot:MessageView:dropdown')
    async def change_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"TODO big decisions starting here {datetime.datetime.now()}",
                                                view=MessageDropdownView())

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


class MessageDropdownView(discord.ui.View):
    def __init__(self, ephemeral=True):
        super().__init__(timeout=None)
        self.ephemeral = ephemeral

    @discord.ui.button(label='Blurple', style=discord.ButtonStyle.blurple, custom_id='me_bot:MessageDropdown:todo43134')
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message('This is blurple.', ephemeral=self.ephemeral)


# More complicated cases might require parsing state out from the custom_id instead.
# For this use case, the library provides a `DynamicItem` to make this easier.
# The same constraints as above apply to this too.
# For this example, the `template` class parameter is used to give the library a regular
# expression to parse the custom_id with.
# These custom IDs will be in the form of e.g. `button:user:80088516616269824`.
class DynamicButton(discord.ui.Button):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            # discord.ui.Button(
            label='Do Thing',
            style=discord.ButtonStyle.blurple,
            custom_id=f'button:user:{user_id}',
            emoji='\N{THUMBS UP SIGN}',
            # )
        )
        self.user_id: int = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'This is your very own button! ({self.user_id})', ephemeral=True)
