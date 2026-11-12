"""SQLite storage for ChalkBox. One file on the box, works fully offline."""

import sqlite3
from contextlib import contextmanager

from app.config import settings

# Status values used by long-running AI jobs:
#   lessons / practice_sheets / reports: queued -> running -> ready -> approved   (or error)
#   submissions: queued -> reading -> needs_review -> grading -> graded -> approved (or error)
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
    language    TEXT NOT NULL DEFAULT 'English'      -- family language for parent notes
);

CREATE TABLE IF NOT EXISTS lessons (
    id          INTEGER PRIMARY KEY,
    class_id    INTEGER NOT NULL REFERENCES classes(id),
    subject     TEXT NOT NULL,
    topic       TEXT NOT NULL,
    params      TEXT NOT NULL,                        -- JSON: grade, minutes, language, ...
    content     TEXT,                                 -- JSON: lesson + worksheet + problems
    status      TEXT NOT NULL DEFAULT 'queued',
    error       TEXT,
    worksheet_id INTEGER REFERENCES worksheets(id),  -- set when the teacher approves
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS worksheets (
    id              INTEGER PRIMARY KEY,
    class_id        INTEGER NOT NULL REFERENCES classes(id),
    lesson_id       INTEGER REFERENCES lessons(id),
    title           TEXT NOT NULL,
    subject         TEXT NOT NULL,
    topic           TEXT NOT NULL,
    questions       TEXT NOT NULL,                    -- JSON list of typed questions + answers
    misconceptions  TEXT NOT NULL,                    -- JSON {id: description}
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id                 INTEGER PRIMARY KEY,
    worksheet_id       INTEGER NOT NULL REFERENCES worksheets(id),
    student_id         INTEGER REFERENCES students(id),
    image_path         TEXT NOT NULL,
    thread_id          TEXT,                          -- LangGraph run id for this check
    student_name_read  TEXT,                          -- name as the AI read it
    status             TEXT NOT NULL DEFAULT 'queued',
    review             TEXT,                          -- JSON: items waiting for the teacher
    feedback           TEXT,
    score_correct      INTEGER,
    score_total        INTEGER,
    error              TEXT,
    created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS answers (
    id              INTEGER PRIMARY KEY,
    submission_id   INTEGER NOT NULL REFERENCES submissions(id),
    question_no     TEXT NOT NULL,
    student_answer  TEXT,
    working         TEXT,
    confidence      REAL,
    correct         INTEGER,                          -- 1, 0, or NULL (undecided)
    graded_by       TEXT,                             -- code | ai | teacher
    misconception   TEXT,
    explanation     TEXT,
    teacher_fixed   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS practice_sheets (
    id            INTEGER PRIMARY KEY,
    worksheet_id  INTEGER NOT NULL REFERENCES worksheets(id),
    student_id    INTEGER NOT NULL REFERENCES students(id),
    content       TEXT,                               -- JSON: intro + questions
    status        TEXT NOT NULL DEFAULT 'queued',
    error         TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id            INTEGER PRIMARY KEY,
    class_id      INTEGER NOT NULL REFERENCES classes(id),
    student_id    INTEGER NOT NULL REFERENCES students(id),
    language      TEXT NOT NULL,
    text          TEXT,
    status        TEXT NOT NULL DEFAULT 'queued',
    error         TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Login accounts. A teacher is linked to a class; a student account to a student row.
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
    display_name   TEXT NOT NULL,
    class_id       INTEGER REFERENCES classes(id),
    student_id     INTEGER REFERENCES students(id),
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Signed-in browsers. Only a hash of the session token is stored.
CREATE TABLE IF NOT EXISTS sessions (
    token_hash   TEXT PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at   TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_students_class ON students(class_id);
CREATE INDEX IF NOT EXISTS idx_submissions_worksheet ON submissions(worksheet_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_answers_submission ON answers(submission_id);
"""


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
