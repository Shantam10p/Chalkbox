"""Accounts and sessions, using only the Python standard library (works offline).

Passwords are stored as PBKDF2-SHA256 hashes. A signed-in browser holds a random session
token in an HttpOnly cookie; the database keeps only a SHA-256 hash of that token.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException

from app.db import connect

COOKIE_NAME = "chalkbox_session"
SESSION_DAYS = 30
_ITERATIONS = 200_000


# ---------------------------------------------------------------- passwords

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# A real hash to check against when the username doesn't exist, so a wrong username
# takes as long as a wrong password (no hint about which accounts exist).
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------------------------------------------------------------- users

def _public(user: dict) -> dict:
    return {k: user[k] for k in ("id", "username", "role", "display_name", "class_id", "student_id")}


def create_user(username: str, password: str, role: str, display_name: str,
                class_id: int | None = None, student_id: int | None = None) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO users (username, password_hash, role, display_name, class_id, student_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username.strip(), hash_password(password), role, display_name, class_id, student_id),
        ).lastrowid


def get_user_by_username(username: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    return dict(row) if row else None


def authenticate(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    return _public(user) if verify_password(password, user["password_hash"]) else None


# ---------------------------------------------------------------- sessions

def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (_now() + timedelta(days=SESSION_DAYS)).isoformat()
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_now().isoformat(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires),
        )
    return token


def end_session(token: str | None) -> None:
    if token:
        with connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def user_for_token(token: str | None) -> dict | None:
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (_token_hash(token), _now().isoformat()),
        ).fetchone()
    return _public(dict(row)) if row else None


# ---------------------------------------------------------------- FastAPI dependencies

def current_user(chalkbox_session: str | None = Cookie(default=None)) -> dict:
    user = user_for_token(chalkbox_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in")
    return user


def require_teacher(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teachers only")
    return user


def require_student(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "student" or user["student_id"] is None:
        raise HTTPException(status_code=403, detail="Students only")
    return user
