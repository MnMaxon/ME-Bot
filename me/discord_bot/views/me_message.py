from typing import List

import discord
import numpy as np

from me.io.db_util import SQLiteDB
from me.message_types import MessageType


class MEMessage:
    _client: discord.Client = None

    def get_message(self):
        raise NotImplementedError("MEMessage is an interface, override get_message()")

    def get_view(self) -> discord.ui.View:
        raise NotImplementedError("MEMessage is an interface, override get_view()")

    def register(self, client: discord.Client):
        self._client = client
        client.add_view(self.get_view())

    def client_check(self):
        if self._client is None:
            raise ValueError("MEMessage must be registered before displaying messages")

    # Provide with discord interaction to reply to command
    async def display(self, channel: int = None, interaction: discord.Interaction = None,
                      ephemeral=False) -> discord.Message:
        self.client_check()
        if channel is None and interaction is not None:
            channel = interaction.channel_id

        if channel is not None and not ephemeral:
            return await self._client.get_channel(channel).send(self.get_message(), view=self.get_view())
        elif interaction is not None:
            delete_after = 5 if ephemeral else None
            return await interaction.response.send_message(self.get_message(), view=self.get_view(),
                                                           ephemeral=ephemeral, delete_after=delete_after)
        else:
            raise ValueError("Either interaction or channel and client must be provided")

    async def update(self, message: discord.Message):
        await message.edit(content=self.get_message(), view=self.get_view())

    def get_db(self) -> SQLiteDB:
        self.client_check()
        return self._client.db


class MEMessageGroup:
    _client = None

    def __init__(self, message_type: MessageType, me_messages: List[MEMessage], max_messages_per_user=10,
                 max_messages_per_server=100, max_messages_per_channel=100, delete_on_startup=False, ephemeral=False):
        self.max_messages_per_channel = max_messages_per_channel
        self._me_messages = me_messages
        self.message_type = message_type
        self.max_messages_per_user = max_messages_per_user
        self.max_messages_per_server = max_messages_per_server
        self.delete_on_startup = delete_on_startup
        self.ephemeral = ephemeral

    def get_me_messages(self) -> List[MEMessage]:
        return self._me_messages

    def register(self, client: discord.Client):
        self._client = client
        for me_message in self.get_me_messages():
            me_message.register(client)
        if self.delete_on_startup:
            message_df = self.get_db().get_messages_of_type_df(self.message_type.value)
            message_and_channel_ids = message_df[['first_message_id', 'channel_id']].unique().tolist()
            for message_id, channel_id in message_and_channel_ids:
                self._client.get_channel(channel_id).delete_messages(message_id)
            self.get_db().delete_messages(message_and_channel_ids)

    async def purge_user_messages(self, user_id: int, server_id: int, max_messages_per_user: int = None):
        if max_messages_per_user is None:
            max_messages_per_user = self.max_messages_per_user
        message_df = self.get_db().get_messages_of_type_and_user_df(self.message_type.value, user_id, server_id)
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while len(message_df.drop_duplicates(['first_message_id', 'channel_id'])) > max_messages_per_user:
            message_df = await self.delete_oldest(message_df)

    async def delete_oldest(self, message_df):
        oldest_msg = message_df['first_message_id'].min()
        old_df = message_df[message_df['first_message_id'] == oldest_msg]
        channel = await self._client.fetch_channel(old_df['channel_id'].iloc[0])
        delete_messages = []
        for msg in old_df['message_id'].values:
            try:
                delete_messages.append(await channel.fetch_message(msg))
            except discord.NotFound:
                pass
        await channel.delete_messages(delete_messages)
        self.get_db().delete_messages(first_message_id=oldest_msg)
        message_df = message_df[message_df['first_message_id'] != oldest_msg]
        return message_df

    async def purge_server_messages(self, server_id: int, max_messages_per_server: int = None):
        if max_messages_per_server is None:
            max_messages_per_server = self.max_messages_per_server
        message_df = self.get_db().get_messages_of_type_df_and_server(self.message_type.value, server_id)
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while len(message_df.drop_duplicates(['first_message_id', 'channel_id'])) > max_messages_per_server:
            message_df = await self.delete_oldest(message_df)

    async def purge_channel_messages(self, channel_id: int, max_messages_per_channel: int = None):
        if max_messages_per_channel is None:
            max_messages_per_channel = self.max_messages_per_channel
        message_df = self.get_db().get_messages_of_type_df_and_channel(self.message_type.value, channel_id)
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while len(message_df.drop_duplicates(['first_message_id', 'channel_id'])) > max_messages_per_channel:
            message_df = await self.delete_oldest(message_df)


    # Provide with discord interaction to reply to command
    async def display(self, user_id: int=None, channel: int = None,
                      interaction: discord.Interaction = None, ephemeral=None) -> List[discord.Message]:
        self.client_check()

        if interaction is not None:
            if channel is None:
                channel = interaction.channel_id
            if user_id is None:
                user_id = interaction.user.id
            self.get_db().add_server(interaction.guild_id)
            self.get_db().add_user(user_id)

        if ephemeral is None:  # TODO WILL NEED TO USE edit_original_response TO UPDATE EPHEMERAL MESSAGES
            ephemeral = self.ephemeral

        messages = []
        for me_message in self.get_me_messages():
            message = await me_message.display(channel=channel, interaction=interaction, ephemeral=ephemeral)
            ephemeral = False  # Only the one message can be ephemeral
            messages.append(message)

        if len(messages) > 0 and not ephemeral:  # Don't save ephemeral messages, they might not be accurate
            message_ids = [message.id for message in messages]
            self.get_db().add_messages(message_ids, self.message_type, messages[0].channel.id, user_id,
                                       server_id=messages[0].guild.id)
            await self.purge_user_messages(user_id, messages[0].guild.id)
            await self.purge_server_messages(messages[0].guild.id)
            await self.purge_channel_messages(messages[0].channel.id)

        if interaction is not None and not interaction.response.is_done():
            try:
                await interaction.response.send_message("Successfully Displayed UI", ephemeral=True, delete_after=0)
            except Exception:
                pass # This can happen if the message is deleted

        return messages

    def get_db(self) -> SQLiteDB:
        self.client_check()
        return self._client.db

    def client_check(self):
        if self._client is None:
            raise ValueError("MEMessageGroup must be registered before displaying messages")
