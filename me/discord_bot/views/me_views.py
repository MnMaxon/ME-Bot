from __future__ import annotations

from typing import List, Collection, Optional, Union

import discord
import numpy as np
from discord import ButtonStyle, Emoji, PartialEmoji

from me.io.db_util import SQLiteDB
from me.message_types import MessageType


class MEView(discord.ui.View):
    _client: discord.Client = None

    def __init__(self, client, *args, **kwargs):
        self._client = client
        super().__init__(*args, **kwargs)

    def get_message(self, **kwargs):
        raise NotImplementedError("MEMessage is an interface, override get_message()")

    def get_view(self, **kwargs) -> discord.ui.View:
        return self

    def get_buttons(self) -> List[discord.ui.Button]:
        return []

    def add_buttons(self):
        for button in self.get_buttons():
            self.add_item(button)

    def register(self, client: discord.Client):
        self._client = client
        client.add_view(self)

    def client_check(self):
        if self._client is None:
            raise ValueError("MEMessage must be registered before displaying messages")

    # Provide with discord interaction to reply to command
    async def display(
        self,
        channel: int = None,
        interaction: discord.Interaction = None,
        ephemeral=False,
        client=None,
    ) -> discord.Message:
        if self._client is None:
            self._client = client
        self.client_check()
        if channel is None and interaction is not None:
            channel = interaction.channel
        channel = self._client.get_channel(channel)

        if channel is not None and not ephemeral:
            return await channel.send(self.get_message(guild=channel.guild), view=self)
        elif interaction is not None:
            delete_after = self.timeout if ephemeral else None
            return await interaction.response.send_message(
                self.get_message(
                    interaction=interaction,
                    guild=interaction.guild,
                    user=interaction.user,
                ),
                view=self,
                ephemeral=ephemeral,
                delete_after=delete_after,
            )
        else:
            raise ValueError(
                "Either interaction or channel and client must be provided"
            )

    async def update(
        self,
        messages: Collection[int | discord.Message] | int | discord.Message,
        channel=None,
    ):
        if not isinstance(messages, Collection):
            messages = [messages]
        channel = self._client.get_channel(channel)
        if channel is None:
            raise ValueError("Channel is required to fetch message by id")
        for message in messages:
            if not isinstance(message, discord.Message):
                message = await channel.fetch_message(int(message))
            await message.edit(content=self.get_message(guild=channel.guild), view=self)

    def get_db(self) -> SQLiteDB:
        self.client_check()
        return self._client.db


class MEViewGroup:
    _client = None

    def __init__(
        self,
        message_type: MessageType,
        views: List[MEView],
        max_messages_per_user=10,
        max_messages_per_server=100,
        max_messages_per_channel=100,
        delete_on_startup=False,
        ephemeral=False,
    ):
        self.max_messages_per_channel = max_messages_per_channel
        self._views = views
        self.message_type = message_type
        self.max_messages_per_user = max_messages_per_user
        self.max_messages_per_server = max_messages_per_server
        self.delete_on_startup = delete_on_startup
        self.ephemeral = ephemeral

    def get_views(self) -> List[MEView]:
        return self._views

    def register(self, client: discord.Client):
        self._client = client
        for view in self.get_views():
            view.register(client)
        if self.delete_on_startup:
            message_df = self.get_db().get_messages_of_type_df(self.message_type.value)
            message_and_channel_ids = (
                message_df[["first_message_id", "channel_id"]].unique().tolist()
            )
            for message_id, channel_id in message_and_channel_ids:
                self._client.get_channel(channel_id).delete_messages(message_id)
            self.get_db().delete_messages(message_and_channel_ids)

    async def purge_user_messages(
        self, user_id: int, server_id: int, max_messages_per_user: int = None
    ):
        if max_messages_per_user is None:
            max_messages_per_user = self.max_messages_per_user
        message_df = self.get_db().get_messages_of_type_and_user_df(
            self.message_type.value, user_id, server_id
        )
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while (
            len(message_df.drop_duplicates(["first_message_id", "channel_id"]))
            > max_messages_per_user
        ):
            message_df = await self.delete_oldest(message_df)

    async def delete_oldest(self, message_df):
        oldest_msg = message_df["first_message_id"].min()
        old_df = message_df[message_df["first_message_id"] == oldest_msg]
        channel = self._client.get_channel(old_df["channel_id"].iloc[0])
        delete_messages = []
        for msg in old_df["message_id"].values:
            try:
                delete_messages.append(await channel.fetch_message(msg))
            except discord.NotFound:
                pass
        await channel.delete_messages(delete_messages)
        self.get_db().delete_messages(first_message_id=oldest_msg)
        message_df = message_df[message_df["first_message_id"] != oldest_msg]
        return message_df

    async def purge_server_messages(
        self, server_id: int, max_messages_per_server: int = None
    ):
        if max_messages_per_server is None:
            max_messages_per_server = self.max_messages_per_server
        message_df = self.get_db().get_messages_of_type_df_and_server(
            self.message_type.value, server_id
        )
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while (
            len(message_df.drop_duplicates(["first_message_id", "channel_id"]))
            > max_messages_per_server
        ):
            message_df = await self.delete_oldest(message_df)

    async def purge_channel_messages(
        self, channel_id: int, max_messages_per_channel: int = None
    ):
        if max_messages_per_channel is None:
            max_messages_per_channel = self.max_messages_per_channel
        message_df = self.get_db().get_messages_of_type_df_and_channel(
            self.message_type.value, channel_id
        )
        message_df["first_message_id"] = message_df["first_message_id"].astype(np.int64)
        while (
            len(message_df.drop_duplicates(["first_message_id", "channel_id"]))
            > max_messages_per_channel
        ):
            message_df = await self.delete_oldest(message_df)

    # Provide with discord interaction to reply to command
    async def display(
        self,
        user_id: int = None,
        channel: int = None,
        interaction: discord.Interaction = None,
        ephemeral=None,
    ) -> List[discord.Message]:
        self.client_check()

        if interaction is not None:
            if channel is None:
                channel = interaction.channel_id
            if user_id is None:
                user_id = interaction.user.id
            self.get_db().add_server(interaction.guild_id)
            self.get_db().add_user(user_id)

        if (
            ephemeral is None
        ):  # TODO WILL NEED TO USE edit_original_response TO UPDATE EPHEMERAL MESSAGES
            ephemeral = self.ephemeral

        messages = []
        for view in self.get_views():
            message = await view.display(
                channel=channel, interaction=interaction, ephemeral=ephemeral
            )
            ephemeral = False  # Only the one message can be ephemeral
            messages.append(message)

        if (
            len(messages) > 0 and not ephemeral
        ):  # Don't save ephemeral messages, they might not be accurate
            message_ids = [message.id for message in messages]
            self.get_db().add_messages(
                message_ids,
                self.message_type,
                messages[0].channel.id,
                user_id,
                server_id=messages[0].guild.id,
            )
            await self.purge_user_messages(user_id, messages[0].guild.id)
            await self.purge_server_messages(messages[0].guild.id)
            await self.purge_channel_messages(messages[0].channel.id)
        if interaction is not None and not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "Successfully Displayed UI", ephemeral=True, delete_after=0
                )
            except Exception:
                pass  # This can happen if the message is deleted

        return messages

    def get_db(self) -> SQLiteDB:
        self.client_check()
        return self._client.db

    def client_check(self):
        if self._client is None:
            raise ValueError(
                "MEMessageGroup must be registered before displaying messages"
            )

    def get_client(self):
        return self._client


class NavButton(discord.ui.Button):
    def __init__(
        self,
        linked_view: Optional[MEView] = None,
        client: discord.Client = None,
        add_location: Optional[str] = "below",  # 'below' or 'above' or None
        custom_id_addon: str = "default",
        ephemeral: bool = True,
        style: ButtonStyle = ButtonStyle.secondary,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        row: Optional[int] = None,
    ) -> None:
        self._client = client
        if custom_id is None:
            custom_id = f"NavButton:label:{custom_id_addon}:{label}"
        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )
        self.ephemeral = ephemeral
        self._linked_view = linked_view

    async def get_linked_view(self, **kwargs):
        return self._linked_view

    async def callback(self, interaction: discord.Interaction) -> None:
        linked_view = await self.get_linked_view(interaction=interaction)
        await linked_view.display(
            client=self._client, interaction=interaction, ephemeral=self.ephemeral
        )
