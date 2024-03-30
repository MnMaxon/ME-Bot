from typing import Optional, Union, Type, Dict, Collection, List

import discord
from discord import ButtonStyle, Emoji, PartialEmoji
import me.discord_bot.views.me_views as me_views
import me.discord_bot.views.items as items


class NavButton(items.MEButton):
    def __init__(
        self,
        linked_view: Optional[Type[me_views.MEView] or me_views.MEView] = None,
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
        self.linked_view = linked_view
        self.replace_message = replace_message

    async def get_context(self, interaction: discord.Interaction, clicked_id=None):
        return {self.label: clicked_id == self.custom_id}

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> me_views.MEView:
        return await get_linked_view(self, interaction, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        return await callback(self, interaction)


class NavSelect(items.MESelect):
    def __init__(
        self,
        options: Dict or Collection,
        linked_view: Optional[Type[me_views.MEView] or me_views.MEView] = None,
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
        self.ephemeral = ephemeral
        self.replace_message = replace_message
        self.linked_view = linked_view
        self._placeholder = placeholder
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
        return {self._placeholder: values}

    async def get_linked_view(
        self, interaction: discord.Interaction = None, **kwargs
    ) -> me_views.MEView:
        return await get_linked_view(self, interaction, **kwargs)

    async def callback(self, interaction: discord.Interaction) -> None:
        return await callback(self, interaction)


# I wanted to put this in a super class for both NavButton and NavSelect, but discord.py gave errors when giving the
# classes multiple inheritance
async def get_linked_view(
    obj: NavButton or NavSelect, interaction: discord.Interaction = None, **kwargs
) -> me_views.MEView:
    if isinstance(obj.linked_view, me_views.MEView):
        return obj.linked_view
    context = await obj.get_view().get_context(interaction, clicked_id=obj.custom_id)
    if isinstance(obj.linked_view, type):
        return obj.linked_view(
            client=obj.get_client(),
            interaction=interaction,
            previous_context=context,
            **kwargs,
        )
    raise TypeError(
        "Linked View must be a me_views.MEView or a Type of me_views.MEView"
    )


async def callback(
    obj: NavButton or NavSelect, interaction: discord.Interaction
) -> None:
    linked_view = await obj.get_linked_view(interaction=interaction)
    await linked_view.display(
        interaction=interaction,
        ephemeral=obj.ephemeral,
        replace_message=obj.replace_message,
    )
