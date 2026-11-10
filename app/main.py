from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="ChalkBox Hub", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    """Shows which models the hub is configured to use (never exposes API keys)."""
    return {
        "hub": "ChalkBox",
        "text_model": {"model": settings.text.model, "base_url": settings.text.base_url},
        "vision_model": {"model": settings.vision.model, "base_url": settings.vision.base_url},
        "thinking_disabled": settings.disable_thinking,
    }


# The teacher web app. Mounted last so the API routes above take priority.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
