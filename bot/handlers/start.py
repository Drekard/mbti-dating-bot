from aiogram import Router, F
from aiogram.types import Message, WebAppInfo
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.database.queries import UserRepo, ProfileRepo, NotificationRepo
from bot.config import ADMIN_IDS, APP_URL

router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    web_app_url = f"{APP_URL}/web" if APP_URL else ""
    rows = [
        [KeyboardButton(text="Моя анкета"), KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Премиум"), KeyboardButton(text="Пригласить друга")],
    ]
    if web_app_url:
        rows.insert(0, [KeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=web_app_url))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(F.text == "/start")
async def cmd_start(message: Message, user, db_session):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Это бот для знакомств по MBTI.\n"
        "Нажми кнопку ниже чтобы открыть приложение!",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "Моя анкета")
async def cmd_my_profile(message: Message, user, db_session):
    profile_repo = ProfileRepo(db_session)
    profile = profile_repo.get_by_user(message.from_user.id)

    if not profile:
        await message.answer(
            "У тебя ещё нет анкеты. Создай её в Mini App!",
            reply_markup=get_main_keyboard(),
        )
        return

    status = "✅ Опубликована" if profile.is_visible and profile.is_approved else "🙈 Скрыта"
    await message.answer(
        f"Твоя анкета: {status}\n"
        f"MBTI: {profile.mbti_type or '[nil]'}\n"
        f"Редактируй в Mini App.",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "Статистика")
async def cmd_stats(message: Message, user, db_session):
    profile_repo = ProfileRepo(db_session)
    stats = profile_repo.get_stats(message.from_user.id)

    if not stats:
        await message.answer("Сначала создай анкету в Mini App!")
        return

    text = (
        f"Твоя статистика:\n\n"
        f"❤️ Лайков получено: {stats['likes_received']}\n"
        f"🤝 Мэтчей: {stats['matches']}\n"
        f"⭐ Средняя оценка: {stats['avg_rating'] or 'нет отзывов'}\n"
        f"📝 Отзывов: {stats['total_reviews']}"
    )
    await message.answer(text)


@router.message(F.text == "Премиум")
async def cmd_premium(message: Message, user, db_session):
    from bot.config import PREMIUM_PRICE_STARS

    is_premium = user.is_premium and user.premium_expires_at and user.premium_expires_at > __import__('datetime').datetime.utcnow()

    if is_premium:
        expires = user.premium_expires_at.strftime("%d.%m.%Y")
        text = f"У тебя премиум до {expires}!"
    else:
        text = f"Премиум — {PREMIUM_PRICE_STARS} Stars\n\nБезлимит просмотров, расширенные фильтры, кто лайкнул меня."

    await message.answer(text)


@router.message(F.text == "Пригласить друга")
async def cmd_referral(message: Message, user, db_session):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    text = (
        f"Твоя реферальная ссылка:\n{ref_link}\n\n"
        f"Приглашённых: {user.referral_count}\n\n"
        "Когда друг создаст анкету — вы оба получите 3 дня премиума!"
    )
    await message.answer(text)


@router.message(F.text == "/app")
async def cmd_app(message: Message, user, db_session):
    from bot.config import APP_URL
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

    if not APP_URL:
        await message.answer(
            "Mini App пока не настроен.\n\n"
            "Для разработчика: укажи APP_URL в .env (например https://xxxx.ngrok-free.app)"
        )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть Mini App", web_app=WebAppInfo(url=f"{APP_URL}/web"))],
    ])
    await message.answer("Открой Mini App:", reply_markup=keyboard)


@router.message(F.text == "Админ")
async def cmd_admin(message: Message, user, db_session):
    if user.id not in ADMIN_IDS:
        return

    notif_repo = NotificationRepo(db_session)
    pending = notif_repo.get_unresolved()
    pending_count = len([p for p in pending if p.type == "new_profile" and not p.is_resolved])

    await message.answer(
        f"📋 Админ-панель\n\n"
        f"⏳ Ожидают: {pending_count}\n\n"
        f"Управляй анкетами через Mini App (admin раздел)."
    )
