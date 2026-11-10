import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ModelEndpoint:
    base_url: str
    api_key: str
    model: str


@dataclass(frozen=True)
class Settings:
    text: ModelEndpoint
    vision: ModelEndpoint
    disable_thinking: bool
    request_timeout: float
    data_dir: Path

    @property
    def db_path(self) -> Path:
        return self.data_dir / "chalkbox.db"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"


def _load_settings() -> Settings:
    text = ModelEndpoint(
        base_url=os.getenv("TEXT_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("TEXT_API_KEY", "ollama"),
        model=os.getenv("TEXT_MODEL", "qwen3:4b"),
    )
    # The vision endpoint falls back to the text endpoint when not set separately.
    vision = ModelEndpoint(
        base_url=os.getenv("VISION_BASE_URL", text.base_url),
        api_key=os.getenv("VISION_API_KEY", text.api_key),
        model=os.getenv("VISION_MODEL", "qwen2.5vl:3b"),
    )
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    return Settings(
        text=text,
        vision=vision,
        disable_thinking=os.getenv("DISABLE_THINKING", "true").lower() == "true",
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "300")),
        data_dir=data_dir,
    )


settings = _load_settings()
