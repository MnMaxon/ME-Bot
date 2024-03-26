from __future__ import annotations

import logging
import os
from typing import Optional, List, Union

import discord
from discord import app_commands, Thread
from discord.abc import PrivateChannel, GuildChannel

from me.discord_bot.role_commands import RoleCommandGroup, RoleView
from me.discord_bot.views import me_views
from me.io import db_util
from me.message_types import MessageType

_logger = logging.getLogger(__name__)


# TODO Scrap permission idea?  Maybe just use the built in discord permissions?
class PermissionGroup(app_commands.Group):
    @app_commands.command()
    async def add(self, interaction: discord.Interaction):
        await interaction.response.send_message("ping")

    @app_commands.command()
    async def list(self, interaction: discord.Interaction):
        await interaction.response.send_message("pong")


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
        self.db: db_util.SQLiteDB | None = None
        self.config = None
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(PermissionGroup())
        self.role_message_group = me_views.MEViewGroup(
            me_views.MessageType.ROLE_MESSAGE,
            [RoleView(client=self)],
            max_messages_per_channel=1,
        )
        self.role_message_group.register(self)
        self.role_group: RoleCommandGroup = RoleCommandGroup(self.role_message_group)
        self.tree.add_command(self.role_group)
        _logger.info(self.tree)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self, guilds: List[int] or None = None):
        if guilds is None:
            guilds = self.get_sync_guilds()
        msg = f"Setting up command hook for guilds specified in the guilds argument: {guilds}"
        _logger.info(msg)
        # This copies the global commands over to your guild.
        for guild_id in guilds:
            guild = await self.fetch_guild(guild_id)
            await self.sync_commands(guild)

        await self.update_messages()

    async def sync_commands(self, guild: discord.Guild, log=True):
        if log:
            _logger.info(f"Syncing commands with {guild.id}")
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    # Returns a list of guilds that sync immediately on startup
    def get_sync_guilds(self) -> List[int]:
        if isinstance(self._sync_guilds, list):
            return self._sync_guilds
        if self._sync_guilds is not None:
            guilds = self._sync_guilds
        else:
            guilds = os.environ.get("ME_RUN_GUILDS", "")
        guilds = guilds.replace(";", ",").replace(" ", ",").split(",")
        guilds = [g.strip() for g in guilds]
        guilds = [int(g) for g in guilds if g != ""]
        return guilds

    def me_setup(self, db, config):
        self.db = db
        self.config = config

    async def update_messages(self):
        df = self.db.get_messages_of_type_df(MessageType.ROLE_MESSAGE)
        me_role_message: RoleView = self.role_group.message_group.get_views()[0]
        for channel_id, df_group in df.groupby("channel_id"):
            channel = await self.fetch_channel(channel_id)
            message_ids = df_group["message_id"].values
            _logger.info(
                f"Updating Role Message for channel {channel_id} with message ids {len(message_ids)}: {message_ids}"
            )
            await me_role_message.update(message_ids, channel)

    # noinspection PyShadowingBuiltins
    def get_channel(
        self, id: Optional[Union[GuildChannel, Thread, PrivateChannel, int]], /
    ) -> Optional[Union[GuildChannel, Thread, PrivateChannel]]:
        _id = id
        _logger.debug(f"Getting Channel {_id}")
        try:
            _id = super().get_channel(int(_id))
        except ValueError:
            pass
        except TypeError:
            pass
        if isinstance(_id, str):
            _logger.info("to int")
            _id = int(_id)
        if isinstance(_id, int):
            _id = super().get_channel(_id)
            _logger.debug(f"\tGot Channel, {_id}")
        return _id


intents = discord.Intents.default()
intents.members = True
client: MEClient = MEClient(intents=intents)


@client.event
async def on_ready():
    _logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    _logger.info("------")


@client.tree.command()
async def meme(interaction: discord.Interaction):
    print("GOT MEME COMMAND!")
    msg = f'Hi, {",".join([str(member) for member in interaction.user.guild.members])}'
    await interaction.response.send_message(msg)


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
    first_value="The first value you want to add something to",
    second_value="The value you want to add to the first value",
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(
        f"{first_value} + {second_value} = {first_value + second_value}"
    )


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send="text")
@app_commands.describe(text_to_send="Text to send in the current channel")
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(
    member="The member you want to get the joined date from; defaults to the user who uses the command"
)
async def joined(
    interaction: discord.Interaction, member: Optional[discord.Member] = None
):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    msg = f"{member} joined {discord.utils.format_dt(member.joined_at)}"
    await interaction.response.send_message(msg)


@client.event
async def on_test_event(**kwargs):
    # Use like client.dispatch("test_event")   <- With optional other args
    _logger.info(f"Called test event with: {kwargs}")
