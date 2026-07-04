import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN, DATABASE_URL, ADMIN_IDS, API_HOST, API_PORT
from bot.database.models import init_db, SessionLocal
from bot.middlewares.auth import AuthMiddleware

from bot.handlers import start

logging.basicConfig(level=logging.INFO)

COMMANDS = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="app", description="Открыть Mini App"),
    BotCommand(command="admin", description="Админ-панель"),
]


def run_api():
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, log_level="info")


async def main():
    init_db()

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logging.info(f"API запущен на http://{API_HOST}:{API_PORT}")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    try:
        await bot.set_my_commands(COMMANDS)
    except Exception as e:
        logging.warning(f"Не удалось зарегистрировать команды: {e}")

    db = SessionLocal()
    dp.update.middleware(AuthMiddleware(db))

    dp.include_router(start.router)

    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
