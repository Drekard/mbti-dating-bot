import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
PREMIUM_PRICE_STARS = int(os.getenv("PREMIUM_PRICE_STARS", "299"))
REFERRAL_BONUS_DAYS = int(os.getenv("REFERRAL_BONUS_DAYS", "3"))
DAILY_VIEW_LIMIT = int(os.getenv("DAILY_VIEW_LIMIT", "10"))
AUTO_APPROVE = os.getenv("AUTO_APPROVE", "true").lower() == "true"
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", os.getenv("PORT", "8000")))
APP_URL = os.getenv("APP_URL", "")
