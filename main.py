import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from handlers.admin import scheduler

from database.models import async_main

from handlers.admin import admin
from handlers.user import user

async def main() -> None:
    bot = Bot(token=os.getenv("TESTS_TOKEN_API"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.include_routers(admin, user)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def on_startup(dispatcher) -> None:
    scheduler.start()
    await async_main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")