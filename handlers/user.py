from aiogram import Router, F
from aiogram.types.message import Message
from aiogram.types import ChatMemberUpdated
from aiogram.filters.command import CommandStart, Command
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION

from database.requests import set_user, mark_user_as_client

user = Router()

@user.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await set_user(message.from_user.id)
    await message.answer("Добро пожаловать!")

@user.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added_to_group(event: ChatMemberUpdated) -> None:
    chat = event.chat
    await set_user(chat.id)