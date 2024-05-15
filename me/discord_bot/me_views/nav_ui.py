from __future__ import annotations

from typing import Optional, Union, Type, Dict, Collection, List, TYPE_CHECKING

import discord
import pandas as pd
from discord import ButtonStyle, Emoji, PartialEmoji
from me.discord_bot.me_views import me_view
import me.discord_bot.me_views.items as items

if TYPE_CHECKING:
    from me.discord_bot.me_client import MEClient


class NavButton(discord.ui.Button, items.Item):
    def __init__(
        self,
        linked_view: Optional[Type[me_view.MEView] or me_view.MEView] = None,
        replace_message: bool = True,
        custom_id_addon: str = "default",
        ephemeral: bool = True,
        style: ButtonStyle = ButtonStyle.secondary,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        row: Optional[int] = None,
        context: Dict = None,
    ) -> None:
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
        items.Item.__init__(self, context=context)
        self.ephemeral = ephemeral
        self.linked_view = linked_view
        self.replace_message = replace_message

    def get_view(self) -> me_view.MEView or None:
        try:
            return self.view
        except AttributeError:
            return None

    def get_client(self) -> MEClient:
        return self.get_view().get_client()

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        return {self.label: clicked_id == self.custom_id}

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> me_view.MEView:
        return await get_linked_view(self, interaction, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        return await callback(self, interaction)


class NavModal(items.MEModal):
    publish_context = False

    def __init__(self, modal_button, **kwargs):
        self.modal_button = modal_button
        super().__init__(**kwargs)

    async def on_submit(self, interaction: discord.Interaction):
        self.publish_context = True
        await self.modal_button.load_view(interaction)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        # Make sure we know what the error actually is
        raise error

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        return self.get_text_values()


class ModalButton(NavButton):
    def __init__(
        self,
        modal: NavModal,
        linked_view: Optional[Type[me_view.MEView] or me_view.MEView] = None,
        allowed_text_inputs: Collection[str] = (),
        disallowed_text_inputs: Collection[str] = (),
        replace_message: bool = True,
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
        self.modal = modal
        self.allowed_text_inputs = allowed_text_inputs
        self.disallowed_text_inputs = disallowed_text_inputs
        super().__init__(
            linked_view=linked_view,
            replace_message=replace_message,
            custom_id_addon=custom_id_addon,
            ephemeral=ephemeral,
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.set_defaults()
        for child in self.modal.children:
            if isinstance(child, discord.ui.TextInput):
                if child.label not in self.allowed_text_inputs:
                    self.modal.remove_item(child)
                if child.label in self.disallowed_text_inputs:
                    self.modal.remove_item(child)
        # Open the modal instead of the view when clicked
        return await interaction.response.send_modal(self.modal)

    # Set the default values of the text inputs to the values from the previous view
    async def set_defaults(self):
        for child in self.modal.children:
            if isinstance(child, discord.ui.TextInput):
                if child.default is None or child.default == "":
                    child.default = self.get_view().previous_context.get(
                        child.label, ""
                    )

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        if not self.modal.publish_context:
            return {}  # Protects from publishing '' values before the modal is submitted
        return self.modal.get_text_values()

    async def load_view(self, interaction: discord.Interaction) -> None:
        return await super().callback(interaction)


class NavSelect(items.MESelect):
    def __init__(
        self,
        options: Dict | Collection | pd.DataFrame,
        linked_view: Optional[Type[me_view.MEView] or me_view.MEView] = None,
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
        if context is None:
            context = {}
        self.previous_context = context
        if default_ids is None:
            default_ids = self.previous_context.get(placeholder, [])
        if not isinstance(default_ids, Collection) or isinstance(default_ids, str):
            default_ids = [default_ids]
        self.ephemeral = ephemeral
        self.replace_message = replace_message
        self.linked_view = linked_view
        self._placeholder = placeholder
        if isinstance(options, pd.DataFrame):
            options = {row[0]: row[1] for row in options.values}
        if isinstance(options, dict):
            self.option_dict = options
        super().__init__(
            options=options,
            custom_id=custom_id,
            custom_id_addon=custom_id_addon,
            placeholder=placeholder,
            default_ids=default_ids,
            *args,
            **kwargs,
        )

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        values = self.values
        if len(values) == 0:  # No values selected, need to get the previous value(s)
            values = self.previous_context.get(self._placeholder, [])
        if values is not None and len(values) == 1 and self.max_values == 1:
            context = {self._placeholder: values[0]}
            if self.option_dict is not None:
                context[self._placeholder + "_desc"] = self.option_dict[int(values[0])]
        else:
            context = {self._placeholder: values}
        return context

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> me_view.MEView:
        return await get_linked_view(self, interaction, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        return await callback(self, interaction)


# I wanted to put this in a super class for both NavButton and NavSelect, but discord.py gave errors when giving the
# classes multiple inheritance
async def get_linked_view(
    obj: NavButton or NavSelect, interaction: discord.Interaction = None, **kwargs
) -> me_view.MEView:
    if isinstance(obj.linked_view, me_view.MEView):
        linked_view = obj.linked_view
        linked_view.previous_view = obj.get_view()
    elif isinstance(obj.linked_view, type):
        context = await obj.get_view().get_context(
            interaction, clicked_id=obj.custom_id
        )
        linked_view = obj.linked_view(
            client=obj.get_client(),
            interaction=interaction,
            previous_context=context,
            previous_view=obj.get_view(),
            **kwargs,
        )
    else:
        raise TypeError(
            "Linked View must be a me_views.MEView or a Type of me_views.MEView"
        )
    return linked_view


async def callback(
    obj: NavButton or NavSelect, interaction: discord.Interaction
) -> None:
    linked_view = await obj.get_linked_view(interaction=interaction)
    await linked_view.display(
        interaction=interaction,
        ephemeral=obj.ephemeral,
        replace_message=obj.replace_message,
    )
