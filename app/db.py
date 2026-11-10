"""SQLite storage for ChalkBox. One file on the box, works fully offline."""

import sqlite3
from contextlib import contextmanager

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS classes (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    grade       INTEGER NOT NULL,
    teacher     TEXT
);

CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY,
    class_id    INTEGER NOT NULL REFERENCES classes(id),
    name        TEXT NOT NULL,
    language    TEXT NOT NULL DEFAULT 'English'   -- family language for parent notes
);

-- A lesson follows the 6-part structure; its body is stored as JSON.
CREATE TABLE IF NOT EXISTS lessons (
    id          INTEGER PRIMARY KEY,
    class_id    INTEGER NOT NULL REFERENCES classes(id),
    topic       TEXT NOT NULL,
    content     TEXT NOT NULL,                     -- JSON: goal, fix_yesterday, teach, ...
    approved    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS worksheets (
    id          INTEGER PRIMARY KEY,
    lesson_id   INTEGER REFERENCES lessons(id),
    title       TEXT NOT NULL,
    questions   TEXT NOT NULL,                     -- JSON list of questions
    answer_key  TEXT NOT NULL,                     -- JSON list of correct answers
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One photographed worksheet from one student.
CREATE TABLE IF NOT EXISTS submissions (
    id            INTEGER PRIMARY KEY,
    worksheet_id  INTEGER NOT NULL REFERENCES worksheets(id),
    student_id    INTEGER REFERENCES students(id),
    image_path    TEXT NOT NULL,
    reading       TEXT,                            -- JSON from the Reader agent
    feedback      TEXT,                            -- per-student feedback text
    status        TEXT NOT NULL DEFAULT 'uploaded', -- uploaded | read | graded | approved
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One row per question per submission.
CREATE TABLE IF NOT EXISTS answers (
    id              INTEGER PRIMARY KEY,
    submission_id   INTEGER NOT NULL REFERENCES submissions(id),
    question_no     INTEGER NOT NULL,
    student_answer  TEXT,
    confidence      REAL,                          -- Reader's confidence, 0..1
    correct         INTEGER,                       -- set by the Checker (code)
    misconception   TEXT,                          -- set by the Diagnoser
    teacher_fixed   INTEGER NOT NULL DEFAULT 0     -- 1 if the teacher corrected the reading
);
"""


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
