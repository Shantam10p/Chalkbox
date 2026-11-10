"""Fills the database with a demo class: Grade 4A (teacher Dave), 30 students, and one
fractions worksheet.

Run from the project root:  python -m scripts.seed          (only if the database is empty)
                            python -m scripts.seed --reset  (wipe everything first)
"""

import sys

from app import repo
from app.config import settings
from app.db import init_db
from scripts.samples import CLASS, FRACTIONS_WORKSHEET, STUDENTS


def reset() -> None:
    for path in (settings.db_path, settings.data_dir / "graphs.db"):
        for suffix in ("", "-wal", "-shm"):
            target = path.with_name(path.name + suffix)
            if target.exists():
                target.unlink()
    for photo in settings.uploads_dir.glob("*"):
        photo.unlink()
    print("Database and uploads cleared.")


def seed() -> None:
    init_db()
    if repo.list_classes():
        print("Database already has data. Use --reset to start over.")
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


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
    seed()
