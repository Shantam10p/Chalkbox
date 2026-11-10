import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.config import settings
from app.db import init_db

STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="ChalkBox Hub", lifespan=lifespan)

# Lets the React dev server (Vite, port 5173) call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "workers": settings.workers,
    }


app.include_router(api_router)

# The teacher web app. Mounted last so the API routes above take priority.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
