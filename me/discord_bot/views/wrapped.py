# from typing import Optional, Union
#
# import discord.ui
# from discord import ButtonStyle, Emoji, PartialEmoji
#
#
# class Button(discord.ui.Button):
#     def __init__(
#             self,
#             replace_message: bool = True,
#             client: discord.Client = None,
#             custom_id_addon: str = "default",
#             style: ButtonStyle = ButtonStyle.secondary,
#             label: Optional[str] = None,
#             disabled: bool = False,
#             custom_id: Optional[str] = None,
#             url: Optional[str] = None,
#             emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
#             row: Optional[int] = None,
#             *args,
#             **kwargs,
#     ) -> None:
#         if custom_id is None:
#             custom_id = f"me:{self.__class__}:{custom_id_addon}:{label}"
#         super(discord.ui.Button).__init__(
#             style=style,
#             label=label,
#             disabled=disabled,
#             custom_id=custom_id,
#             url=url,
#             emoji=emoji,
#             row=row,
#         )
#         self.replace_message = replace_message
#         self._client = client
#
# class Item:
#     def __init__(
#             self,
#             replace_message: bool = True,
#             client: discord.Client = None,
#             custom_id_addon: str = "default",
#             ephemeral: bool = True,
#             style: ButtonStyle = ButtonStyle.secondary,
#             label: Optional[str] = None,
#             disabled: bool = False,
#             custom_id: Optional[str] = None,
#             url: Optional[str] = None,
#             emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
#             row: Optional[int] = None,
#             *args,
#             **kwargs,
#     ) -> None:
