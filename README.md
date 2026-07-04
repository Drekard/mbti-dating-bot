# MBTI Dating — Mini App

Telegram Mini App для знакомств по MBTI типам.

## Архитектура

```
┌─────────────────┐     REST API      ┌─────────────────┐
│   Telegram      │ ◄──────────────► │   FastAPI       │
│   Mini App      │   (JSON)         │   + Static      │
│   (HTML/JS)     │                  │   (web/)        │
└─────────────────┘                  └────────┬────────┘
                                             │
                                      ┌──────▼──────┐
                                      │ PostgreSQL  │
                                      │ / SQLite    │
                                      └─────────────┘
                                             ▲
                                             │ уведомления
                                      ┌──────┴──────┐
                                      │ Telegram    │
                                      │ Bot (push)  │
                                      └─────────────┘
```

## Установка

1. Клонируй репозиторий
2. `cp .env.example .env` и заполни токен
3. `pip install -r requirements.txt`
4. `python -m bot.main`

API запустится на `http://localhost:8000`, бот — polling.

## Настройка Mini App

1. Открой @BotFather → /mybots → выбери бота → Bot Settings → Menu Button
2. URL: `https://your-domain.ru/web` (или ngrok для тестов)
3. Text: `Открыть`

Для локального теста: `ngrok http 8000` → получишь HTTPS URL.

## Структура

```
├── api/                    # FastAPI REST API
│   ├── main.py             # Точка входа API
│   ├── auth.py             # Telegram initData валидация
│   ├── schemas.py          # Pydantic модели
│   └── routes/
│       ├── profiles.py     # Профиль CRUD
│       ├── browse.py       # Просмотр, лайки, статистика
│       └── admin.py        # Админ-эндпоинты
├── bot/                    # Telegram bot (уведомления)
│   ├── main.py             # Точка входа бота + API
│   ├── config.py           # Настройки
│   ├── notifications.py    # Push-уведомления
│   ├── database/
│   │   ├── models.py       # SQLAlchemy модели
│   │   └── queries.py      # Репозитории
│   ├── handlers/
│   │   └── start.py        # /start, кнопки
│   └── middlewares/
│       └── auth.py         # Авторизация
├── web/                    # Mini App фронтенд
│   └── index.html          # Single-page app
├── requirements.txt
├── Dockerfile
└── .env.example
```

## API Endpoints

### Профиль
- `GET /api/profile/me` — получить свой профиль
- `POST /api/profile/create` — создать/обновить профиль
- `POST /api/profile/publish` — опубликовать
- `POST /api/profile/hide` — скрыть
- `DELETE /api/profile/delete` — удалить

### Просмотр
- `GET /api/browse?mbti_filter=INTJ&limit=10` — листать анкеты
- `POST /api/like` — лайк/дизлайк `{target_user_id, like_type}`
- `GET /api/stats` — статистика
- `GET /api/who-liked-me` — кто лайкнул (премиум)

### Админ
- `GET /api/admin/profiles/new` — новые анкеты
- `GET /api/admin/profiles/all` — все анкеты
- `POST /api/admin/approve/{user_id}` — одобрить
- `POST /api/admin/hide/{user_id}` — скрыть
- `POST /api/admin/ban/{user_id}` — забанить
- `GET /api/admin/stats` — статистика

### Авторизация
Все запросы требуют заголовок `X-Telegram-Init-Data` с данными из Telegram WebApp.

## Деплой на Render

1. Подключи репозиторий
2. Добавь переменные окружения
3. Создай PostgreSQL
4. URL: `https://your-app.onrender.com`
5. В BotFather укажи `https://your-app.onrender.com/web`

## Команды бота

- `/start` — главная кнопка Mini App
- `/admin` — админ-панель (только ADMIN_IDS)
