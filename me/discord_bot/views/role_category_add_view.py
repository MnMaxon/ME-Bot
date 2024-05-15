import re

import discord

from me.const.emoji import CRITICAL, CHECK
from me.discord_bot.me_views.me_view import MEView
from me.discord_bot.me_views.nav_ui import NavModal, ModalButton
from me.me_util import validate_emoji


class RoleCategoryAddModal(NavModal):
    def __init__(self, title="Add Role Category", **kwargs):
        super().__init__(title=title,**kwargs)
        category_name = discord.ui.TextInput(
            label="Category Name",
            placeholder="Enter a category name",
            max_length=100,
            required=True,
        )
        emoji = discord.ui.TextInput(
            label="Category Emoji",
            placeholder="Paste emoji here (format -> :star:)",
            required=False,
        )
        self.add_item(category_name)
        self.add_item(emoji)


class RoleCategoryAddButton(ModalButton):
    def __init__(
            self, label="New Category", style=discord.ButtonStyle.blurple, **kwargs
    ):
        modal = RoleCategoryAddModal(modal_button=self)
        print(modal.to_components())
        super().__init__(
            modal=modal, label=label, style=style, linked_view=RoleCategoryAddView, **kwargs
        )


class RoleCategoryAddView(MEView):
    def __init__(self, **kwargs):
        super().__init__(timeout=2 * 60, **kwargs)
        self.bonus_msg = ""
        try:
            category = self.get_category()
            if category != "":
                emoji = self.get_emoji()
                if emoji != "":
                    emoji += " "
                self.add_category()
                self.bonus_msg += f"{CHECK}  Created Category: {emoji}{category}\n"
                self.timeout = 10
        except ValueError as e:
            self.bonus_msg += f"{CRITICAL}  {e}\n"
            category = ""

        if category == "":
            add_button = RoleCategoryAddButton()
            self.add_item(add_button)
        self.add_back_button()

    def add_category(self):
        category = self.get_category()
        emoji = self.get_emoji()
        if emoji == "":
            emoji = None
        else:
            emoji = emoji[1:-1]
        self.get_client().db.add_role_category(
            self.previous_interaction.guild_id, category, emoji
        )

    def get_message(self, interaction=None, **kwargs):
        msg = ":desktop:  **Add Role Category**\n" + self.bonus_msg
        return msg

    def get_category(self):
        cat = self.previous_context.get("Category Name", "")
        cat = re.sub(r"[^a-zA-Z0-9_\-\ ]", "", cat)
        return cat

    def get_emoji(self):
        emoji = self.previous_context.get("Category Emoji", "")
        emoji = validate_emoji(emoji)
        return emoji
