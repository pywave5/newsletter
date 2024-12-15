from typing import List, Dict, Union
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup
)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Union


class InlineKeyboardsControl:

    @classmethod
    async def create_keyboards(cls,
                               buttons: List[Dict[str, Union[str, None]]],
                               row_width: int = 2) -> InlineKeyboardMarkup:

        if row_width <= 0:
            raise ValueError("row_width должен быть больше нуля.")

        inline_keyboard = []
        row = []

        for index, button in enumerate(buttons, start=1):
            text = button.get("text")
            callback = button.get("callback")
            url = button.get("url")

            if not text:
                raise ValueError("Кнопка должна содержать текст.")
            if not callback and not url:
                raise ValueError(f"Кнопка '{text}' должна содержать либо callback, либо url.")

            row.append(InlineKeyboardButton(text=text, callback_data=callback, url=url))

            if index % row_width == 0:
                inline_keyboard.append(row)
                row = []

        if row:
            inline_keyboard.append(row)

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @classmethod
    async def create_keyboard(cls,
                              text: str,
                              callback: str | None = None,
                              url: str | None = None
                              ) -> InlineKeyboardMarkup:
        if not text:
            raise ValueError("Кнопка должна содержать текст.")
        if not callback and not url:
            raise ValueError(f"Кнопка '{text}' должна содержать либо callback, либо url.")

        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback, url=url)]
        ])

        return ikb

class ReplyKeyboardsControl:

    @classmethod
    async def create_keyboards(cls,
                              row: int,
                              texts: List[str]
                              ) -> ReplyKeyboardMarkup:
        if row <= 0:
            raise ValueError("Количество кнопок в строке должно быть больше нуля.")

        keyboard = [
            [KeyboardButton(text=texts[i + j]) for j in range(row) if i + j < len(texts)]
            for i in range(0, len(texts), row)
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

    @classmethod
    async def create_keyboard(cls,
                              text: str
                              ) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=text)]
        ], resize_keyboard=True, one_time_keyboard=True)
        return kb