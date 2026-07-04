import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

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

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

db = SessionLocal()
dp.update.middleware(AuthMiddleware(db))

dp.include_router(start.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    try:
        await bot.set_my_commands(COMMANDS)
    except Exception as e:
        logging.warning(f"Не удалось зарегистрировать команды: {e}")

    if APP_URL:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True, secret_token="mbti-dating-secret")
        logging.info(f"Webhook установлен: {WEBHOOK_URL}")
    else:
        logging.warning("APP_URL не задан — бот не будет работать")

    yield

    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(title="MBTI Dating", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "MBTI Dating API", "docs": "/docs"}


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header != "mbti-dating-secret":
        return Response(status_code=401)
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return Response(status_code=200)


app.mount("/web", StaticFiles(directory="web", html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot.main:app", host=API_HOST, port=API_PORT, log_level="info")
