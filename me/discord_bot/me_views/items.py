from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Collection, List
from me.discord_bot.me_views.me_view import MEView
import discord.ui

if TYPE_CHECKING:
    from me.discord_bot.me_client import MEClient


class MEModal(discord.ui.Modal):
    def get_text_inputs(self) -> List[discord.ui.TextInput]:
        return [
            child for child in self.children if isinstance(child, discord.ui.TextInput)
        ]

    def get_text_values(self) -> Dict[str, str]:
        # custom_id ?
        return {ti.label: ti.value for ti in self.get_text_inputs()}


class MESelect(discord.ui.Select):
    def __init__(
        self,
        options: Dict or Collection,
        default_ids: List = None,
        custom_id: str = None,
        custom_id_addon: str = None,
        placeholder: str = None,
        *args,
        **kwargs,
    ):
        if custom_id is None:
            custom_id = f"me:{self.__class__.__name__}:{custom_id_addon}:{placeholder}"
        super().__init__(custom_id=custom_id, placeholder=placeholder, *args, **kwargs)
        if isinstance(options, Dict):
            self.option_dict = options
            options = options.items()
        if default_ids is None:
            default_ids = []
        else:
            default_ids = [str(i) for i in default_ids]
        for item in options:
            val = item[0]
            if val is not None:
                val = str(val)
            self.add_option(label=str(item[1]), value=val, default=val in default_ids)

    def get_view(self) -> MEView:
        return self.view

    def get_client(self) -> MEClient:
        return self.get_view().get_client()


class Item:
    def __init__(self, context=None):
        if context is None:
            context = {}
        self.previous_context = context

    async def get_context(self, interaction: discord.Interaction, **kwargs):
        return {}
