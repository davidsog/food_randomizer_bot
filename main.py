import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.engine import create_db

# Импортируем роутеры
from handlers.admin_private import admin_router
from handlers.user_private import user_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def on_startup(bot):
    print("Подключение к базе данных...")
    await create_db()
    print("База данных готова!")

async def main():
    dp.startup.register(on_startup)

    # --- ВОТ ЭТО САМОЕ ВАЖНОЕ ---
    # Порядок важен! Сначала админ, потом юзер
    dp.include_router(admin_router)
    dp.include_router(user_router)
    # ----------------------------

    print("Бот запущен и готов к работе!") 
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")