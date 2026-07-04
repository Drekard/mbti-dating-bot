import hashlib
import hmac
import json
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from urllib.parse import unquote

from bot.database.queries import UserRepo, ProfileRepo
from bot.database.models import SessionLocal
from bot.config import BOT_TOKEN

router = APIRouter()


def validate_telegram_init_data(init_data: str) -> dict:
    parsed = {}
    for part in init_data.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            parsed[unquote(key)] = unquote(value)

    hash_check = parsed.pop("hash", None)
    if not hash_check:
        raise HTTPException(status_code=401, detail="No hash in init_data")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if calculated_hash != hash_check:
        raise HTTPException(status_code=401, detail="Invalid hash")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Init data expired")

    user_data = json.loads(parsed.get("user", "{}"))
    return user_data


class AuthResult:
    def __init__(self, user_id: int, user_data: dict):
        self.user_id = user_id
        self.user_data = user_data


def get_current_user(x_telegram_init_data: str = Header(...)) -> AuthResult:
    try:
        user_data = validate_telegram_init_data(x_telegram_init_data)
    except HTTPException:
        raise

    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user id")

    db = SessionLocal()
    try:
        user_repo = UserRepo(db)
        user = user_repo.get_or_create(
            user_id=int(user_id),
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
        )

        if user.is_banned:
            raise HTTPException(status_code=403, detail="User is banned")

        return AuthResult(user_id=int(user_id), user_data=user_data)
    finally:
        db.close()
