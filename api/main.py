import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from bot.database.models import init_db
from api.routes import profiles, browse, admin

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MBTI Dating API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(profiles.router)
app.include_router(browse.router)
app.include_router(admin.router)

app.mount("/web", StaticFiles(directory="web", html=True), name="web")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "MBTI Dating API", "docs": "/docs"}
