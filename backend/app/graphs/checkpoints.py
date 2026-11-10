"""Shared SQLite checkpoint store, so paused graphs survive restarts (fully offline)."""

import sqlite3
from functools import lru_cache

from langgraph.checkpoint.sqlite import SqliteSaver

from app.config import settings


@lru_cache(maxsize=1)
def get_checkpointer() -> SqliteSaver:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.data_dir / "graphs.db", check_same_thread=False)
    return SqliteSaver(conn)
