"""What a signed-in student can see: only their own work, and only after the teacher approved it."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import analysis, helper, repo
from app.api.common import found
from app.auth import require_student
from app.config import settings
from app.misconceptions import with_defaults

router = APIRouter(prefix="/me", tags=["student"])
log = logging.getLogger("chalkbox.helper")


class HelperIn(BaseModel):
    message: str = Field(min_length=1, max_length=helper.MAX_MESSAGE_CHARS)


@router.get("/helper")
def helper_history(user: dict = Depends(require_student)):
    return [
        {k: m[k] for k in ("id", "role", "content", "created_at")}
        for m in repo.helper_messages(user["student_id"], limit=50)
    ]


@router.post("/helper")
def ask_helper(body: HelperIn, user: dict = Depends(require_student)):
    """Ask the course helper a question. Hints only; off-topic questions are declined."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Type a question first")
    if repo.helper_messages_since(user["student_id"], 60) >= helper.MESSAGES_PER_HOUR:
        raise HTTPException(status_code=429, detail="That's a lot of questions! Take a break and try again later.")

    try:
        answer = helper.reply(user["student_id"], message)
    except Exception as error:
        log.exception("Helper failed for student %s", user["student_id"])
        raise HTTPException(status_code=503, detail="The helper is busy right now. Try again in a moment.") from error

    repo.add_helper_message(user["student_id"], "student", message,
                            on_topic=answer["on_topic"], flagged=answer["flagged"])
    message_id = repo.add_helper_message(user["student_id"], "helper", answer["reply"])
    return {"id": message_id, "role": "helper", "content": answer["reply"]}


def _own_approved_submission(submission_id: int, user: dict) -> dict:
    submission = repo.get_submission(submission_id)
    # Same 404 for "not yours" and "doesn't exist", so nothing leaks about other students.
    if submission is None or submission["student_id"] != user["student_id"] or submission["status"] != "approved":
        raise HTTPException(status_code=404, detail="Worksheet not found")
    return submission


@router.get("")
def overview(user: dict = Depends(require_student)):
    student = found(repo.get_student(user["student_id"]), "Student")
    class_ = repo.get_class(student["class_id"])
    return {
        "student": student,
        "class": {"name": class_["name"], "grade": class_["grade"], "teacher": class_["teacher"]},
        "work_count": len(repo.student_submissions(user["student_id"], ("approved",))),
        "practice_count": len(repo.student_practice(user["student_id"])),
    }


@router.get("/work")
def my_work(user: dict = Depends(require_student)):
    return repo.student_submissions(user["student_id"], ("approved",))


@router.get("/work/{submission_id}")
def my_work_detail(submission_id: int, user: dict = Depends(require_student)):
    submission = _own_approved_submission(submission_id, user)
    worksheet = repo.get_worksheet(submission["worksheet_id"])
    questions = {str(q["number"]): q for q in worksheet["questions"]}
    mistakes = with_defaults(worksheet["misconceptions"])
    return {
        "id": submission["id"],
        "title": worksheet["title"],
        "subject": worksheet["subject"],
        "date": submission["created_at"],
        "score_correct": submission["score_correct"],
        "score_total": submission["score_total"],
        "feedback": submission["feedback"],
        "answers": [
            {
                "question_no": a["question_no"],
                "question": questions.get(a["question_no"], {}).get("text", ""),
                "your_answer": a["student_answer"],
                "correct": a["correct"],
                # The right answer is shown only for questions the student got wrong.
                "correct_answer": questions.get(a["question_no"], {}).get("answer") if a["correct"] is False else None,
                "mistake": mistakes.get(a["misconception"]) if a["correct"] is False and a["misconception"] not in (None, "other") else None,
                "explanation": a["explanation"] if a["correct"] is False else None,
            }
            for a in submission["answers"]
        ],
    }


@router.get("/work/{submission_id}/image")
def my_work_image(submission_id: int, user: dict = Depends(require_student)):
    submission = _own_approved_submission(submission_id, user)
    path = settings.data_path(submission["image_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo file is missing")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/practice")
def my_practice(user: dict = Depends(require_student)):
    sheets = repo.student_practice(user["student_id"])
    # Hide answers: students should work them out themselves.
    for sheet in sheets:
        content = sheet.get("content") or {}
        content["questions"] = [
            {k: v for k, v in q.items() if k in ("number", "text", "type", "options")}
            for q in content.get("questions", [])
        ]
    return sheets


@router.get("/progress")
def my_progress(user: dict = Depends(require_student)):
    profile = found(analysis.student_profile(user["student_id"], approved_only=True), "Student")
    return {k: profile[k] for k in ("history", "average", "trend", "top_mistakes")}
