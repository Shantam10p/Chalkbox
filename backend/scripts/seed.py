"""Fills the database with a demo class: Grade 4A (teacher Dave), 30 students, one fractions
worksheet, and two login accounts (teacher Dave and student Maya Johnson).

Run from the backend folder:
    python -m scripts.seed          (adds the demo class if empty; always adds missing accounts)
    python -m scripts.seed --reset  (wipe everything first)
"""

import sys

from app import auth, repo
from app.config import settings
from app.db import init_db
from scripts.samples import ACCOUNTS, CLASS, FRACTIONS_WORKSHEET, STUDENTS


def reset() -> None:
    for path in (settings.db_path, settings.data_dir / "graphs.db"):
        for suffix in ("", "-wal", "-shm"):
            target = path.with_name(path.name + suffix)
            if target.exists():
                target.unlink()
    for photo in settings.uploads_dir.glob("*"):
        photo.unlink()
    print("Database and uploads cleared.")


def seed_class() -> None:
    if repo.list_classes():
        print("Class data already exists (use --reset to start over).")
        return
    class_id = repo.create_class(CLASS["name"], CLASS["grade"], CLASS["teacher"])
    for name, language in STUDENTS:
        repo.add_student(class_id, name, language)
    worksheet_id = repo.create_worksheet(
        class_id, FRACTIONS_WORKSHEET["title"], FRACTIONS_WORKSHEET["subject"],
        FRACTIONS_WORKSHEET["topic"], FRACTIONS_WORKSHEET["questions"],
        FRACTIONS_WORKSHEET["misconceptions"],
    )
    print(f"Created class {class_id} ({CLASS['name']}, teacher {CLASS['teacher']}), "
          f"{len(STUDENTS)} students, worksheet {worksheet_id}.")


def seed_accounts() -> None:
    """Adds the demo logins if they are missing. Safe to run on a database with real data."""
    class_ = repo.list_classes()[0]
    students = {s["name"]: s["id"] for s in repo.list_students(class_["id"])}
    for account in ACCOUNTS:
        if auth.get_user_by_username(account["username"]):
            print(f"Account '{account['username']}' already exists.")
            continue
        student_id = None
        if account["role"] == "student":
            student_id = students.get(account["student"])
            if student_id is None:
                print(f"Skipped '{account['username']}': no student named {account['student']}.")
                continue
        auth.create_user(
            account["username"], account["password"], account["role"], account["display_name"],
            class_id=class_["id"], student_id=student_id,
        )
        print(f"Created {account['role']} account '{account['username']}' "
              f"(password: {account['password']}).")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
    init_db()
    seed_class()
    seed_accounts()
