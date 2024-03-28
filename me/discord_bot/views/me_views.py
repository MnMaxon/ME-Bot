from __future__ import annotations

from typing import List, Collection, Optional, Union, Type, Dict

import discord
import numpy as np
from discord import ButtonStyle, Emoji, PartialEmoji
from typing_extensions import deprecated

from me.io.db_util import SQLiteDB
from me.message_types import MessageType


class MEView(discord.ui.View):
    _client: discord.Client = None

    def __init__(
        self,
        client,
        interaction=None,
        previous_context=None,
        persistent_context=(),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if previous_context is None:
            previous_context = {}
        self._client = client
        self.previous_context = previous_context
        self.persistent_context = persistent_context

    async def get_context(
        self, interaction: discord.Interaction, clicked_id=None
    ) -> Dict:
        context = {}
        if self.persistent_context is not None:
            for key in self.persistent_context:
                if key in self.previous_context:
                    context[key] = self.previous_context[key]
        for item in self.children:
            if isinstance(item, NavButton) or isinstance(item, NavSelect):
                item_context = await item.get_context(
                    interaction, clicked_id=clicked_id
                )
                context.update(item_context)
        return context

    def get_persistent_context(self) -> str:
        return self.persistent_context

    def get_message(self, **kwargs):
        raise NotImplementedError("MEMessage is an interface, override get_message()")

    @deprecated
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
            raise ValueError(
                f"MEMessage must be registered before displaying messages {self.__class__.__name__}"
            )

    # Provide with discord interaction to reply to command
    async def display(
        self,
        channel: int = None,
        interaction: discord.Interaction = None,
        ephemeral=False,
        client=None,
        replace_message=False,
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
            msg = self.get_message(
                interaction=interaction,
                guild=interaction.guild,
                user=interaction.user,
            )
            if replace_message:
                await interaction.response.defer()
                return await interaction.edit_original_response(content=msg, view=self)
            return await interaction.response.send_message(
                msg,
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

    def add_nav_button(
        self,
        label: str,
        linked_view: Type[MEView] or MEView,
        replace_message=True,
        client=None,
        **kwargs,
    ):
        if self._client is None:
            self._client = client
        btn = NavButton(
            label=label,
            linked_view=linked_view,
            client=self._client,
            **kwargs,
            replace_message=replace_message,
        )
        self.add_item(btn)
        return btn


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
        linked_view: Optional[Type[MEView] or MEView] = None,
        replace_message: bool = True,
        client: discord.Client = None,
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
            custom_id = f"me:{self.__class__.__name__}:{custom_id_addon}:{label}"
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
        self.replace_message = replace_message

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        return {self.label: clicked_id == self.custom_id}

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> MEView:
        if isinstance(self._linked_view, MEView):
            return self._linked_view

        context = {}
        if isinstance(self.view, MEView):
            context = await self.view.get_context(
                interaction, clicked_id=self.custom_id
            )
        if isinstance(self._linked_view, type):
            return self._linked_view(
                client=self._client,
                interaction=interaction,
                previous_context=context,
                **kwargs,
            )
        raise TypeError("Linked View must be a MEView or a Type of MEView")

    async def callback(self, interaction: discord.Interaction) -> None:
        linked_view = await self.get_linked_view(interaction=interaction)
        await linked_view.display(
            client=self._client,
            interaction=interaction,
            ephemeral=self.ephemeral,
            replace_message=self.replace_message,
        )


class MESelect(discord.ui.Select):
    def __init__(
        self,
        items: Dict or Collection,
        client: discord.Client,
        default_ids: List = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if isinstance(items, Dict):
            items = items.items()
        if default_ids is None:
            default_ids = []
        else:
            default_ids = [str(i) for i in default_ids]
        for item in items:
            val = item[0]
            if val is not None:
                val = str(val)
            self.add_option(label=str(item[1]), value=val, default=val in default_ids)
        self._client = client


class NavSelect(MESelect):
    def __init__(
        self,
        items: Dict or Collection,
        client: discord.Client,
        linked_view: Optional[Type[MEView] or MEView] = None,
        context: Dict = None,
        default_ids: List = None,
        ephemeral: bool = True,
        replace_message: bool = True,
        placeholder: Optional[str] = None,
        custom_id: str = None,
        custom_id_addon: str = None,
        *args,
        **kwargs,
    ):
        if context == None:
            context = {}
        self.previous_context = context
        if default_ids is None:
            default_ids = self.previous_context.get(placeholder, [])
        self.ephemeral = ephemeral
        self.replace_message = replace_message
        self._linked_view = linked_view
        if custom_id is None:
            custom_id = f"me:{self.__class__.__name__}:{custom_id_addon}:{placeholder}"
        self._placeholder = placeholder
        super().__init__(
            items=items,
            client=client,
            custom_id=custom_id,
            placeholder=placeholder,
            default_ids=default_ids,
            *args,
            **kwargs,
        )

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        values = self.values
        if len(values) == 0:  # No values selected, need to get the previous value(s)
            values = self.previous_context.get(self._placeholder, [])
        return {self._placeholder: values}

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> MEView:
        if isinstance(self._linked_view, MEView):
            return self._linked_view
        context = {}
        if isinstance(self.view, MEView):
            context = await self.view.get_context(interaction)
        if isinstance(self._linked_view, type):
            return self._linked_view(
                client=self._client,
                interaction=interaction,
                previous_context=context,
                **kwargs,
            )
        raise TypeError("Linked View must be a MEView or a Type of MEView")

    async def callback(self, interaction: discord.Interaction) -> None:
        linked_view = await self.get_linked_view(interaction=interaction)
        await linked_view.display(
            client=self._client,
            interaction=interaction,
            ephemeral=self.ephemeral,
            replace_message=self.replace_message,
        )
