import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import router as api_router
from app.config import PROJECT_ROOT, settings
from app.db import init_db

# The React build (frontend/dist) when it exists, otherwise the simple placeholder page.
REACT_BUILD = PROJECT_ROOT / "frontend" / "dist"
WEB_DIR = REACT_BUILD if (REACT_BUILD / "index.html").exists() else Path(__file__).parent / "static"


class SinglePageApp(StaticFiles):
    """Serves the React app; unknown paths like /plan return index.html for React Router."""

    async def get_response(self, path, scope):
        # Unknown API paths must stay real 404s, not turn into the web page.
        normalized = path.replace("\\", "/")  # Windows passes backslashes here
        is_api = normalized == "api" or normalized.startswith("api/")
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as error:
            if error.status_code != 404 or is_api:
                raise
            return await super().get_response("index.html", scope)
        if response.status_code == 404 and not is_api:
            return await super().get_response("index.html", scope)
        return response

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
app.mount("/", SinglePageApp(directory=WEB_DIR, html=True), name="web")
