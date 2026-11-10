"""Database helpers. Graphs and API routes use these instead of writing SQL."""

import difflib
import json
from typing import Any

from app.db import connect

_UPDATABLE = {
    "lessons": {"content", "status", "error", "worksheet_id"},
    "submissions": {"student_id", "thread_id", "student_name_read", "status", "review",
                    "feedback", "score_correct", "score_total", "error"},
    "practice_sheets": {"content", "status", "error"},
    "reports": {"text", "status", "error"},
}
_JSON_FIELDS = {"params", "content", "questions", "misconceptions", "review"}


def _dump(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def _row(row) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    for field in _JSON_FIELDS & data.keys():
        if data[field] is not None:
            data[field] = json.loads(data[field])
    return data


def _rows(rows) -> list[dict]:
    return [_row(r) for r in rows]


def _update(table: str, row_id: int, fields: dict) -> None:
    unknown = set(fields) - _UPDATABLE[table]
    if unknown:
        raise ValueError(f"Cannot update {table}.{', '.join(sorted(unknown))}")
    if not fields:
        return
    values = [_dump(v) if k in _JSON_FIELDS else v for k, v in fields.items()]
    assignments = ", ".join(f"{k} = ?" for k in fields)
    if table == "submissions":
        assignments += ", updated_at = CURRENT_TIMESTAMP"
    with connect() as conn:
        conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", [*values, row_id])


# ---------------------------------------------------------------- classes and students

def create_class(name: str, grade: int, teacher: str | None = None) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO classes (name, grade, teacher) VALUES (?, ?, ?)", (name, grade, teacher)
        ).lastrowid


def list_classes() -> list[dict]:
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT c.*, COUNT(s.id) AS student_count FROM classes c "
            "LEFT JOIN students s ON s.class_id = c.id GROUP BY c.id ORDER BY c.id"
        ))


def get_class(class_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM classes WHERE id = ?", (class_id,)).fetchone())


def add_student(class_id: int, name: str, language: str = "English") -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO students (class_id, name, language) VALUES (?, ?, ?)",
            (class_id, name, language),
        ).lastrowid


def list_students(class_id: int) -> list[dict]:
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT * FROM students WHERE class_id = ? ORDER BY name", (class_id,)
        ))


def get_student(student_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone())


def match_student(class_id: int, name: str) -> int | None:
    """Finds the student whose name best matches what the AI read on the worksheet."""
    if not (name or "").strip():
        return None
    students = list_students(class_id)
    by_name = {s["name"].casefold(): s["id"] for s in students}
    read = name.casefold().strip()
    if read in by_name:
        return by_name[read]
    # Also try first names only, since students often write just their first name.
    first_names = {}
    for s in students:
        first_names.setdefault(s["name"].split()[0].casefold(), []).append(s["id"])
    if read in first_names and len(first_names[read]) == 1:
        return first_names[read][0]
    close = difflib.get_close_matches(read, list(by_name), n=1, cutoff=0.75)
    return by_name[close[0]] if close else None


# ---------------------------------------------------------------- worksheets

def create_worksheet(class_id: int, title: str, subject: str, topic: str,
                     questions: list[dict], misconceptions: dict[str, str],
                     lesson_id: int | None = None) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO worksheets (class_id, lesson_id, title, subject, topic, questions, "
            "misconceptions) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (class_id, lesson_id, title, subject, topic, _dump(questions), _dump(misconceptions)),
        ).lastrowid


def get_worksheet(worksheet_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM worksheets WHERE id = ?", (worksheet_id,)).fetchone())


def list_worksheets(class_id: int | None = None) -> list[dict]:
    query = (
        "SELECT w.id, w.class_id, w.lesson_id, w.title, w.subject, w.topic, w.created_at, "
        "COUNT(s.id) AS submission_count FROM worksheets w "
        "LEFT JOIN submissions s ON s.worksheet_id = w.id"
    )
    params: tuple = ()
    if class_id is not None:
        query += " WHERE w.class_id = ?"
        params = (class_id,)
    query += " GROUP BY w.id ORDER BY w.id DESC"
    with connect() as conn:
        return _rows(conn.execute(query, params))


def latest_graded_worksheet(class_id: int) -> int | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT w.id FROM worksheets w JOIN submissions s ON s.worksheet_id = w.id "
            "WHERE w.class_id = ? AND s.status IN ('graded', 'approved') "
            "ORDER BY w.id DESC LIMIT 1",
            (class_id,),
        ).fetchone()
    return row["id"] if row else None


# ---------------------------------------------------------------- submissions

def create_submission(worksheet_id: int, image_path: str) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO submissions (worksheet_id, image_path) VALUES (?, ?)",
            (worksheet_id, image_path),
        ).lastrowid


def update_submission(submission_id: int, **fields) -> None:
    _update("submissions", submission_id, fields)


def get_submission(submission_id: int) -> dict | None:
    with connect() as conn:
        sub = _row(conn.execute(
            "SELECT s.*, st.name AS student_name FROM submissions s "
            "LEFT JOIN students st ON st.id = s.student_id WHERE s.id = ?",
            (submission_id,),
        ).fetchone())
        if sub:
            sub["answers"] = _answer_rows(conn, submission_id)
    return sub


def _answer_rows(conn, submission_id: int) -> list[dict]:
    rows = _rows(conn.execute(
        "SELECT question_no, student_answer, working, confidence, correct, graded_by, "
        "misconception, explanation, teacher_fixed FROM answers WHERE submission_id = ? "
        "ORDER BY CAST(question_no AS INTEGER), question_no",
        (submission_id,),
    ))
    for row in rows:
        row["correct"] = None if row["correct"] is None else bool(row["correct"])
        row["teacher_fixed"] = bool(row["teacher_fixed"])
    return rows


def list_submissions(worksheet_id: int, with_answers: bool = False) -> list[dict]:
    with connect() as conn:
        subs = _rows(conn.execute(
            "SELECT s.*, st.name AS student_name FROM submissions s "
            "LEFT JOIN students st ON st.id = s.student_id "
            "WHERE s.worksheet_id = ? ORDER BY s.id",
            (worksheet_id,),
        ))
        if with_answers:
            for sub in subs:
                sub["answers"] = _answer_rows(conn, sub["id"])
    return subs


def save_check_state(submission_id: int, class_id: int, state: dict) -> None:
    """Stores what the Check graph produced so far (readings, marks, feedback)."""
    sub = get_submission(submission_id)
    fields: dict[str, Any] = {"student_name_read": state.get("student_name") or None}
    if sub and sub.get("student_id") is None:
        fields["student_id"] = match_student(class_id, state.get("student_name") or "")
    if "feedback" in state:
        fields["feedback"] = state.get("feedback")
    if "score_correct" in state:
        fields["score_correct"] = state["score_correct"]
        fields["score_total"] = state["score_total"]
    update_submission(submission_id, **fields)

    results = state.get("results") or {}
    with connect() as conn:
        conn.execute("DELETE FROM answers WHERE submission_id = ?", (submission_id,))
        conn.executemany(
            "INSERT INTO answers (submission_id, question_no, student_answer, working, confidence, "
            "correct, graded_by, misconception, explanation, teacher_fixed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    submission_id, number, r.get("answer"), r.get("working"), r.get("confidence"),
                    None if r.get("correct") is None else int(bool(r["correct"])),
                    r.get("graded_by"), r.get("misconception"), r.get("explanation"),
                    int(bool(r.get("teacher_fixed"))),
                )
                for number, r in results.items()
            ],
        )


def approve_submission(submission_id: int, student_id: int | None,
                       overrides: dict[str, bool], feedback: str | None) -> None:
    """Teacher sign-off: optional mark overrides, edited feedback, and the student link."""
    with connect() as conn:
        for number, correct in overrides.items():
            conn.execute(
                "UPDATE answers SET correct = ?, graded_by = 'teacher' "
                "WHERE submission_id = ? AND question_no = ?",
                (int(bool(correct)), submission_id, str(number)),
            )
        row = conn.execute(
            "SELECT COUNT(*) AS total, SUM(correct = 1) AS right FROM answers WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
    fields: dict[str, Any] = {
        "status": "approved",
        "score_correct": row["right"] or 0,
        "score_total": row["total"],
    }
    if student_id is not None:
        fields["student_id"] = student_id
    if feedback is not None:
        fields["feedback"] = feedback
    update_submission(submission_id, **fields)


def student_answers(student_id: int) -> list[dict]:
    """Every graded answer by one student, newest worksheet last."""
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT s.id AS submission_id, s.worksheet_id, w.title, w.topic, s.created_at, "
            "s.score_correct, s.score_total, a.question_no, a.correct, a.misconception "
            "FROM submissions s JOIN worksheets w ON w.id = s.worksheet_id "
            "LEFT JOIN answers a ON a.submission_id = s.id "
            "WHERE s.student_id = ? AND s.status IN ('graded', 'approved') "
            "ORDER BY s.id, CAST(a.question_no AS INTEGER)",
            (student_id,),
        ))


# ---------------------------------------------------------------- lessons

def create_lesson(class_id: int, subject: str, topic: str, params: dict) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO lessons (class_id, subject, topic, params) VALUES (?, ?, ?, ?)",
            (class_id, subject, topic, _dump(params)),
        ).lastrowid


def update_lesson(lesson_id: int, **fields) -> None:
    _update("lessons", lesson_id, fields)


def get_lesson(lesson_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone())


def list_lessons(class_id: int) -> list[dict]:
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT id, class_id, subject, topic, status, worksheet_id, created_at "
            "FROM lessons WHERE class_id = ? ORDER BY id DESC",
            (class_id,),
        ))


# ---------------------------------------------------------------- practice sheets and reports

def create_practice(worksheet_id: int, student_id: int) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO practice_sheets (worksheet_id, student_id) VALUES (?, ?)",
            (worksheet_id, student_id),
        ).lastrowid


def update_practice(practice_id: int, **fields) -> None:
    _update("practice_sheets", practice_id, fields)


def get_practice(practice_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute(
            "SELECT p.*, st.name AS student_name FROM practice_sheets p "
            "JOIN students st ON st.id = p.student_id WHERE p.id = ?",
            (practice_id,),
        ).fetchone())


def list_practice(worksheet_id: int) -> list[dict]:
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT p.*, st.name AS student_name FROM practice_sheets p "
            "JOIN students st ON st.id = p.student_id WHERE p.worksheet_id = ? ORDER BY st.name",
            (worksheet_id,),
        ))


def create_report(class_id: int, student_id: int, language: str) -> int:
    with connect() as conn:
        return conn.execute(
            "INSERT INTO reports (class_id, student_id, language) VALUES (?, ?, ?)",
            (class_id, student_id, language),
        ).lastrowid


def update_report(report_id: int, **fields) -> None:
    _update("reports", report_id, fields)


def get_report(report_id: int) -> dict | None:
    with connect() as conn:
        return _row(conn.execute(
            "SELECT r.*, st.name AS student_name FROM reports r "
            "JOIN students st ON st.id = r.student_id WHERE r.id = ?",
            (report_id,),
        ).fetchone())


def list_reports(class_id: int) -> list[dict]:
    with connect() as conn:
        return _rows(conn.execute(
            "SELECT r.*, st.name AS student_name FROM reports r "
            "JOIN students st ON st.id = r.student_id WHERE r.class_id = ? ORDER BY r.id DESC",
            (class_id,),
        ))
