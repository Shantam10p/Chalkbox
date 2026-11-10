"""Runs the slow AI work (graphs) in the background so the API answers instantly.

WORKERS in .env sets how many jobs run at once: 1 on a laptop, more on a DGX Spark.
Every job records its progress in the database (status / error), which the API reports.
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from langgraph.types import Command

from app import analysis, repo
from app.config import settings
from app.graphs import check_graph, followup_graph, plan_graph

log = logging.getLogger("chalkbox.jobs")
_executor = ThreadPoolExecutor(max_workers=settings.workers, thread_name_prefix="chalkbox-job")


def submit(job, *args) -> None:
    def run():
        try:
            job(*args)
        except Exception:  # each job stores its own error; this only logs surprises
            log.exception("Background job %s%s crashed", job.__name__, args)

    _executor.submit(run)


def new_thread_id(submission_id: int) -> str:
    return f"submission-{submission_id}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------- Check graph

def run_check(submission_id: int, resume: dict | None = None) -> None:
    submission = repo.get_submission(submission_id)
    worksheet = repo.get_worksheet(submission["worksheet_id"])
    config = {"configurable": {"thread_id": submission["thread_id"]}}
    repo.update_submission(submission_id, status="reading" if resume is None else "grading", error=None)

    try:
        if resume is None:
            output = check_graph().invoke(
                {
                    "image_path": str(settings.data_path(submission["image_path"])),
                    "questions": worksheet["questions"],
                    "misconceptions": worksheet["misconceptions"],
                },
                config,
            )
        else:
            output = check_graph().invoke(Command(resume=resume), config)

        repo.save_check_state(submission_id, worksheet["class_id"], output)
        if "__interrupt__" in output:
            repo.update_submission(submission_id, status="needs_review",
                                   review=output["__interrupt__"][0].value)
        else:
            repo.update_submission(submission_id, status="graded", review=None)
    except Exception as error:
        log.exception("Check failed for submission %s", submission_id)
        repo.update_submission(submission_id, status="error", error=str(error)[:500])


# ---------------------------------------------------------------- Plan graph

def run_lesson(lesson_id: int) -> None:
    lesson = repo.get_lesson(lesson_id)
    params = lesson["params"]
    class_ = repo.get_class(lesson["class_id"])
    repo.update_lesson(lesson_id, status="running", error=None)

    try:
        output = plan_graph().invoke({
            "subject": lesson["subject"],
            "topic": lesson["topic"],
            "grade": class_["grade"],
            "minutes": params.get("minutes", 40),
            "num_questions": params.get("num_questions", 8),
            "language": params.get("language") or "English",
            "recent_mistakes": analysis.recent_mistakes(lesson["class_id"])
            if params.get("fix_yesterday", True) else [],
        })
        content = {
            "lesson": output.get("lesson", {}),
            "worksheet": {
                "title": params.get("title") or lesson["topic"],
                "questions": output.get("questions", []),
                "misconceptions": output.get("misconceptions", {}),
            },
            "problems": output.get("problems", []),
        }
        if content["worksheet"]["questions"]:
            repo.update_lesson(lesson_id, content=content, status="ready")
        else:
            repo.update_lesson(lesson_id, content=content, status="error",
                               error="The AI did not produce any usable worksheet questions.")
    except Exception as error:
        log.exception("Lesson %s failed", lesson_id)
        repo.update_lesson(lesson_id, status="error", error=str(error)[:500])


# ---------------------------------------------------------------- Follow-up graph

def run_practice(practice_id: int, num_questions: int = 4) -> None:
    practice = repo.get_practice(practice_id)
    worksheet = repo.get_worksheet(practice["worksheet_id"])
    class_ = repo.get_class(worksheet["class_id"])
    repo.update_practice(practice_id, status="running", error=None)

    try:
        output = followup_graph().invoke({
            "kind": "practice",
            "student_name": practice["student_name"],
            "grade": class_["grade"],
            "subject": worksheet["subject"],
            "topic": worksheet["topic"],
            "mistakes": analysis.student_mistakes_on(worksheet["id"], practice["student_id"]),
            "num_questions": num_questions,
        })
        sheet = output.get("practice") or {}
        if sheet.get("questions"):
            repo.update_practice(practice_id, content=sheet, status="ready")
        else:
            repo.update_practice(practice_id, content=sheet, status="error",
                                 error="The AI did not produce any usable practice questions.")
    except Exception as error:
        log.exception("Practice sheet %s failed", practice_id)
        repo.update_practice(practice_id, status="error", error=str(error)[:500])


def run_report(report_id: int) -> None:
    report = repo.get_report(report_id)
    class_ = repo.get_class(report["class_id"])
    profile = analysis.student_profile(report["student_id"])
    repo.update_report(report_id, status="running", error=None)

    try:
        output = followup_graph().invoke({
            "kind": "report",
            "student_name": report["student_name"],
            "grade": class_["grade"],
            "subject": "",
            "topic": "",
            "language": report["language"],
            "teacher": class_.get("teacher"),
            "profile": {
                "history": "; ".join(f"{h['title']}: {h['score']}" for h in profile["history"]),
                "top_mistakes": "; ".join(m["description"] for m in profile["top_mistakes"][:3]),
                "trend": profile["trend"],
            },
        })
        repo.update_report(report_id, text=output.get("report", ""), status="ready")
    except Exception as error:
        log.exception("Report %s failed", report_id)
        repo.update_report(report_id, status="error", error=str(error)[:500])
