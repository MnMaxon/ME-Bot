from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from me.discord_bot.me_client import MEClient

from typing import List, Collection, Type, Dict

import discord
import numpy as np

from me.io.db_util import SQLiteDB
from me.message_types import MessageType
from discord.ui import View


class MEView(View):
    """
    A class to represent a view in the discord bot.

    Attributes
    ----------
    _client : MEClient
        The discord client.
    interaction : discord.Interaction
        The previous interaction.
    previous_context : dict
        The previous context of the view.
    previous_view : MEView
        The previous view.
    persistent_context : Collection[str]
        Keys that will be held consistently when the view is reloaded.

    Methods
    -------
    get_context(interaction: discord.Interaction, clicked_id=None) -> Dict:
        Returns the context of the view.
    get_persistent_context() -> str:
        Returns the persistent context of the view.
    get_message(**kwargs):
        Raises NotImplementedError. This method should be overridden in a subclass.
    get_view(**kwargs) -> View:
        Returns the view.
    register(client: MEClient):
        Registers the view with the discord client.
    client_check():
        Checks if the view is registered with a client.
    display(channel: int = None, interaction: discord.Interaction = None, ephemeral=False, client=None, replace_message=False) -> discord.Message:
        Displays the view.
    update(messages: Collection[int | discord.Message] | int | discord.Message, channel=None):
        Updates the view.
    get_db() -> SQLiteDB:
        Returns the database.
    add_nav_button(label: str, linked_view: Type[MEView] or MEView, replace_message=True, client=None, **kwargs):
        Adds a navigation button to the view.
    """

    _client: MEClient | None = None

    def __init__(
        self,
        client,
        interaction: discord.Interaction = None,
        previous_context=None,
        previous_view=None,
        persistent_context=(),
        *args,
        **kwargs,
    ):
        """
        Constructs all the necessary attributes for the MEView object.

        Parameters
        ----------
            client : MEClient
                The discord client.
            interaction : discord.Interaction, optional
                The interaction that triggered the view (default is None).
            previous_context : dict, optional
                The previous context of the view (default is None).
            persistent_context : Collection[str]
        Keys that will be held consistently when the view is reloaded.
        """
        super().__init__(*args, **kwargs)
        if previous_context is None:
            previous_context = {}
        self._client = client
        self.previous_context = previous_context
        self.previous_view = previous_view
        self.persistent_context = persistent_context
        self.previous_interaction = interaction

    async def get_context(
        self, interaction: discord.Interaction, clicked_id=None
    ) -> Dict:
        """
        Returns the context of the view.

        Parameters
        ----------
            interaction : discord.Interaction
                The interaction that triggered the view.
            clicked_id : str, optional
                The id of the clicked item (default is None).

        Returns
        -------
            context : dict
                The context of the view.
        """
        context = {}
        if self.persistent_context is not None:
            for key in self.persistent_context:
                if key in self.previous_context:
                    context[key] = self.previous_context[key]
        from me.discord_bot.views import nav_ui

        for item in self.children:
            if isinstance(item, nav_ui.NavButton) or isinstance(item, nav_ui.NavSelect):
                item_context = await item.get_context(
                    interaction, clicked_id=clicked_id
                )
                if item_context is not None:
                    context.update(item_context)
            elif isinstance(item, discord.ui.TextInput):
                context[item.label] = item.value
        return context

    def get_persistent_context(self) -> Collection[str]:
        """
        Returns the persistent context of the view.

        Returns
        -------
            Collection[str]
                The persistent context of the view.
        """
        return self.persistent_context

    def get_message(self, interaction: discord.Interaction = None, **kwargs):
        """
        Raises NotImplementedError. This method should be overridden in a subclass.

        Parameters
        ----------
            interaction : discord.Interaction
                The interaction that triggered the view.
            *args : dict
                Arbitrary arguments.
            **kwargs : dict
                Arbitrary keyword arguments.

        Raises
        ------
            NotImplementedError
                If the method is not overridden in a subclass.
        """
        raise NotImplementedError("MEMessage is an interface, override get_message()")

    def register(self, client: MEClient):
        """
        Registers the view with the discord client.

        Parameters
        ----------
            client : MEClient
                The discord client.
        """
        self._client = client
        client.add_view(self)

    def client_check(self):
        """
        Checks if the view is registered with a client.

        Raises
        ------
            ValueError
                If the view is not registered with a client.
        """
        if self.get_client() is None:
            raise ValueError(
                f"MEMessage must be registered before displaying messages {self.__class__.__name__}"
            )

    # Provide with discord interaction to reply to command
    async def display(
        self,
        channel: int = None,
        interaction: discord.Interaction = None,
        ephemeral=False,
        replace_message=False,
    ) -> discord.Message:
        """
        Displays the view.

        Parameters
        ----------
            channel : int, optional
                The id of the channel where the view will be displayed (default is None).
            interaction : discord.Interaction, optional
                The interaction that triggered the view (default is None).
            ephemeral : bool, optional
                Whether the view is ephemeral (default is False).
            replace_message : bool, optional
                Whether to replace the message (default is False).

        Returns
        -------
            discord.Message
                The message that was sent.

        Raises
        ------
            ValueError
                If neither interaction nor channel and client are provided.
        """
        self.client_check()
        self.previous_interaction = interaction
        if channel is None and interaction is not None:
            channel = interaction.channel
        channel = self.get_client().get_channel(channel)

        if channel is not None and not ephemeral:
            kwargs = {"guild": channel.guild}
            return await channel.send(
                self.get_message(interaction=interaction, **kwargs),
                view=self,
            )
        elif interaction is not None:
            delete_after = self.timeout if ephemeral else None
            kwargs = {"guild": channel.guild, "user": interaction.user}
            msg = self.get_message(interaction=interaction, **kwargs)
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
        """
        Updates the view.

        Parameters
        ----------
            messages : Collection[int | discord.Message] | int | discord.Message
                The messages to update.
            channel : int, optional
                The id of the channel where the messages are located (default is None).

        Raises
        ------
            ValueError
                If the channel is not provided.
        """
        if not isinstance(messages, Collection):
            messages = [messages]
        channel = self.get_client().get_channel(channel)
        if channel is None:
            raise ValueError("Channel is required to fetch message by id")
        for message in messages:
            if not isinstance(message, discord.Message):
                message = await channel.fetch_message(int(message))
            await message.edit(
                content=self.get_message(interaction=None, **{"guild": channel.guild}),
                view=self,
            )

    def get_db(self) -> SQLiteDB:
        """
        Returns the database.

        Returns
        -------
            SQLiteDB
                The database.
        """
        self.client_check()
        return self.get_client().db

    def add_nav_button(
        self,
        label: str,
        linked_view: Type[MEView] or MEView,
        replace_message=True,
        row: int = None,
        disabled=False,
        **kwargs,
    ):
        """
        Adds a navigation button to the view.

        Parameters
        ----------
            label : str
                The label of the button.
            linked_view : Type[MEView] or MEView
                The view that the button is linked to.
            replace_message : bool, optional
                Whether to replace the message (default is True).
            client : MEClient, optional
                The discord client (default is None).
            row: int, optional
                The row of the button (default is None).
            disabled : bool, optional
                Whether the button is disabled (default is False).
            **kwargs : dict
                Arbitrary keyword arguments.

        Returns
        -------
            nav_ui.NavButton
                The navigation button that was added.
        """
        from me.discord_bot.views import nav_ui

        btn = nav_ui.NavButton(
            label=label,
            linked_view=linked_view,
            replace_message=replace_message,
            row=row,
            disabled=disabled,
            **kwargs,
        )
        self.add_item(btn)
        return btn

    def add_back_button(self, ignore_error=False, **kwargs):
        """
        Adds a back button to the view.

        Parameters
        ----------
            ignore_error : bool, optional
                Whether to ignore the error if there is no previous view (default is False).
            **kwargs : dict
                Arbitrary keyword arguments.
        """
        if not ignore_error and self.previous_view is None:
            raise ValueError("No previous view to go back to")
        self.add_nav_button(label="Back", linked_view=self.previous_view, **kwargs)

    def get_client(self):
        return self._client


class MEViewGroup:
    """
    A class to represent a group of views in the discord bot.

    Attributes
    ----------
    _client : MEClient
        The discord client.
    _views : List[MEView]
        The views in the group.
    message_type : MessageType
        The type of the message.
    max_messages_per_user : int
        The maximum number of messages per user.
    max_messages_per_server : int
        The maximum number of messages per server.
    max_messages_per_channel : int
        The maximum number of messages per channel.
    delete_on_startup : bool
        Whether to delete the messages on startup.
    ephemeral : bool
        Whether the messages are ephemeral.

    Methods
    -------
    get_views() -> List[MEView]:
        Returns the views in the group.
    register(client: MEClient):
        Registers the group with the discord client.
    purge_user_messages(user_id: int, server_id: int, max_messages_per_user: int = None):
        Purges the user's messages.
    delete_oldest(message_df):
        Deletes the oldest message.
    purge_server_messages(server_id: int, max_messages_per_server: int = None):
        Purges the server's messages.
    purge_channel_messages(channel_id: int, max_messages_per_channel: int = None):
        Purges the channel's messages.
    display(user_id: int = None, channel: int = None, interaction: discord.Interaction = None, ephemeral=None) -> List[discord.Message]:
        Displays the group.
    get_db() -> SQLiteDB:
        Returns the database.
    client_check():
        Checks if the group is registered with a client.
    get_client():
        Returns the client.
    """

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
        """
        Constructs all the necessary attributes for the MEViewGroup object.

        Parameters
        ----------
            message_type : MessageType
                The type of the message.
            views : List[MEView]
                The views in the group.
            max_messages_per_user : int, optional
                The maximum number of messages per user (default is 10).
            max_messages_per_server : int, optional
                The maximum number of messages per server (default is 100).
            max_messages_per_channel : int, optional
                The maximum number of messages per channel (default is 100).
            delete_on_startup : bool, optional
                Whether to delete the messages on startup (default is False).
            ephemeral : bool, optional
                Whether the messages are ephemeral (default is False).
        """
        self.max_messages_per_channel = max_messages_per_channel
        self._views = views
        self.message_type = message_type
        self.max_messages_per_user = max_messages_per_user
        self.max_messages_per_server = max_messages_per_server
        self.delete_on_startup = delete_on_startup
        self.ephemeral = ephemeral

    def get_views(self) -> List[MEView]:
        """
        Returns the views in the group.

        Returns
        -------
            List[MEView]
                The views in the group.
        """
        return self._views

    def register(self, client: MEClient):
        """
        Registers the group with the discord client.

        Parameters
        ----------
            client : MEClient
                The discord client.
        """
        self._client = client
        for view in self.get_views():
            view.register(client)
        if self.delete_on_startup:
            message_df = self.get_db().get_messages_of_type_df(self.message_type.value)
            message_and_channel_ids = (
                message_df[["first_message_id", "channel_id"]].unique().tolist()
            )
            for message_id, channel_id in message_and_channel_ids:
                self.get_client().get_channel(channel_id).delete_messages(message_id)
            self.get_db().delete_messages(message_and_channel_ids)

    async def purge_user_messages(
        self, user_id: int, server_id: int, max_messages_per_user: int = None
    ):
        """
        Purges the user's messages.

        Parameters
        ----------
            user_id : int
                The id of the user.
            server_id : int
                The id of the server.
            max_messages_per_user : int, optional
                The maximum number of messages per user (default is None).
        """
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
        """
        Deletes the oldest message.

        Parameters
        ----------
            message_df : DataFrame
                The DataFrame containing the messages.

        Returns
        -------
            message_df : DataFrame
                The DataFrame containing the messages after the oldest one was deleted.
        """
        oldest_msg = message_df["first_message_id"].min()
        old_df = message_df[message_df["first_message_id"] == oldest_msg]
        channel = self.get_client().get_channel(old_df["channel_id"].iloc[0])
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

        if ephemeral is None:
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
        return self.get_client().db

    def client_check(self):
        if self.get_client() is None:
            raise ValueError(
                "MEMessageGroup must be registered before displaying messages"
            )

    def get_client(self):
        return self._client
