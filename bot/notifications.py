from bot.database.queries import UserRepo, ProfileRepo
from bot.database.models import SessionLocal
from bot.config import ADMIN_IDS, BOT_TOKEN
from bot.keyboards.inline import get_main_keyboard


async def notify_match(bot, user_id: int, match_user_id: int):
    try:
        db = SessionLocal()
        profile_repo = ProfileRepo(db)
        match_profile = profile_repo.get_by_user(match_user_id)

        if match_profile:
            text = f"🎉 Мэтч!\n\n{match_profile.mbti_type}, {match_profile.age or ''}, {match_profile.communication_form or ''}"
            await bot.send_message(user_id, text)
        db.close()
    except Exception:
        pass


async def notify_new_profile(bot, user_id: int):
    try:
        await bot.send_message(user_id, "Твоя анкета опубликована! ✅\nТеперь она видна другим пользователям.")
    except Exception:
        pass


async def notify_admins(bot, db_session, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, message)
        except Exception:
            pass


async def notify_complaint(bot, admin_id: int, message: str):
    try:
        await bot.send_message(admin_id, f"🚨 Жалоба:\n{message}")
    except Exception:
        pass
