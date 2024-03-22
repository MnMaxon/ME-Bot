import logging
import os
from typing import Optional, List

import discord
from discord import app_commands

from me.discord_bot.role_commands import RoleGroup

_logger = logging.getLogger(__name__)


# TODO Scrap permission idea?  Maybe just use the built in discord permissions?
class PermissionGroup(app_commands.Group):
    @app_commands.command()
    async def add(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"ping")

    @app_commands.command()
    async def list(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"pong")


class MEClient(discord.Client):
    _sync_guilds: str | None = None

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.db = None
        self.config = None
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(PermissionGroup())
        self.tree.add_command(RoleGroup(self))
        _logger.info(self.tree)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self, guilds: List[int] or None = None):
        if guilds is None:
            guilds = self.get_sync_guilds()
        _logger.info(f"Setting up command hook for guilds specified in the guilds argument: {guilds}")
        # This copies the global commands over to your guild.
        for guild_id in guilds:
            guild = await self.fetch_guild(guild_id)
            await self.sync_commands(guild)

    async def sync_commands(self, guild: discord.Guild, log=True):
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        if log:
            _logger.info(f"Synced commands with {guild} ({guild.id})")

    # Returns a list of guilds that sync immediately on startup
    def get_sync_guilds(self) -> List[int]:
        if isinstance(self._sync_guilds, list):
            return self._sync_guilds
        if self._sync_guilds is not None:
            guilds = self._sync_guilds
        else:
            guilds = os.environ.get('ME_RUN_GUILDS', '')
        guilds = guilds.replace(";", ",").replace(" ", ",").split(",")
        guilds = [g.strip() for g in guilds]
        guilds = [int(g) for g in guilds if g != ""]
        return guilds

    def me_setup(self, db, config):
        self.db = db
        self.config = config


intents = discord.Intents.default()
intents.members = True
client: MEClient = MEClient(intents=intents)


@client.event
async def on_ready():
    _logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    _logger.info('------')


@client.tree.command()
async def meme(interaction: discord.Interaction):
    print("GOT MEME COMMAND 3!")
    """Says hello!"""
    await interaction.response.send_message(
        f'Hi, {",".join([str(member) for member in interaction.user.guild.members])}')


# @client.group()
# async def permission(interaction: discord.Interaction):
#     print("GOT PERM COMMAND!")
#     """Says hello!"""
#     await interaction.response.send_message(f'Hi, {client.users}')


# @permission.command()
# async def add(interaction: discord.Interaction, first_value: int, second_value: int):
#     """Adds two numbers together."""
#     await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined {discord.utils.format_dt(member.joined_at)}')


@client.event
async def on_test_event(**kwargs):
    # Use like client.dispatch("test_event")   <- With optional other args
    _logger.info(f"Called test event with: {kwargs}")

# These Context menu commands look cool

# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
# @client.tree.context_menu(name='Show Join Date')
# async def show_join_date(interaction: discord.Interaction, member: discord.Member):
#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')


# This context menu command only works on messages
# @client.tree.context_menu(name='Report to Moderators')
# async def report_message(interaction: discord.Interaction, message: discord.Message):
#     # We're sending this response message with ephemeral=True, so only the command executor can see it
#     await interaction.response.send_message(
#         f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
#     )
#
#     # Handle report by sending it into a log channel
#     log_channel = interaction.guild.get_channel(0)  # replace with log channel id
#
#     embed = discord.Embed(title='Reported Message')
#     if message.content:
#         embed.description = message.content
#
#     embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
#     embed.timestamp = message.created_at
#
#     url_view = discord.ui.View()
#     url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
#
#     await log_channel.send(embed=embed, view=url_view)
