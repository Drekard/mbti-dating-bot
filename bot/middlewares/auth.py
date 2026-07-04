from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from sqlalchemy.orm import Session

from bot.database.queries import UserRepo


class AuthMiddleware(BaseMiddleware):
    def __init__(self, db_session: Session):
        self.db = db_session

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user

        if not user:
            return await handler(event, data)

        referred_by = None
        if event.message and event.message.text and event.message.text.startswith("/start ") and len(event.message.text.split()) > 1:
            try:
                referred_by = int(event.message.text.split()[1])
            except (ValueError, IndexError):
                referred_by = None

        user_repo = UserRepo(self.db)
        db_user = user_repo.get_or_create(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            referred_by=referred_by,
        )

        if db_user.is_banned:
            if event.message:
                await event.message.answer("Вы заблокированы.")
            elif event.callback_query:
                await event.callback_query.answer("Вы заблокированы.")
            return

        data["user"] = db_user
        data["db_session"] = self.db
        return await handler(event, data)
