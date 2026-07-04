import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import BOT_TOKEN, ADMIN_IDS, API_HOST, API_PORT, APP_URL
from bot.database.models import init_db, SessionLocal
from bot.middlewares.auth import AuthMiddleware
from bot.handlers import start

logging.basicConfig(level=logging.INFO)

COMMANDS = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="app", description="Открыть Mini App"),
    BotCommand(command="admin", description="Админ-панель"),
]

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}" if APP_URL else ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    bot = Bot(token=BOT_TOKEN)
    try:
        await bot.set_my_commands(COMMANDS)
    except Exception as e:
        logging.warning(f"Не удалось зарегистрировать команды: {e}")

    if APP_URL:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logging.info(f"Webhook установлен: {WEBHOOK_URL}")
    else:
        logging.warning("APP_URL не задан — бот не будет работать")

    yield

    await bot.session.close()


app = FastAPI(title="MBTI Dating", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

db = SessionLocal()
dp.update.middleware(AuthMiddleware(db))

dp.include_router(start.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "MBTI Dating API", "docs": "/docs"}


webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
app.add_route(WEBHOOK_PATH, webhook_handler, methods=["POST"])

setup_application(app, dp, bot=bot)

app.mount("/web", StaticFiles(directory="web", html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot.main:app", host=API_HOST, port=API_PORT, log_level="info")
