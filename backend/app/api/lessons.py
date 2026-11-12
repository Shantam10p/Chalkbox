from fastapi import APIRouter

from app import jobs, repo
from app.api.common import found, require_status
from app.misconceptions import with_defaults
from app.schemas import ApproveLessonIn, LessonIn

router = APIRouter(tags=["lessons"])


@router.post("/lessons", status_code=202)
def create_lesson(body: LessonIn):
    """Starts the Plan graph: 5-part lesson + worksheet + answer key, in the background."""
    found(repo.get_class(body.class_id), "Class")
    params = body.model_dump(exclude={"class_id", "subject", "topic"})
    lesson_id = repo.create_lesson(body.class_id, body.subject, body.topic, params)
    jobs.submit(jobs.run_lesson, lesson_id)
    return {"id": lesson_id, "status": "queued"}


@router.get("/lessons")
def list_lessons(class_id: int):
    return repo.list_lessons(class_id)


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int):
    return found(repo.get_lesson(lesson_id), "Lesson")


@router.post("/lessons/{lesson_id}/approve")
def approve_lesson(lesson_id: int, body: ApproveLessonIn):
    """Teacher approves the lesson (with optional edits); its worksheet becomes gradable."""
    lesson = found(repo.get_lesson(lesson_id), "Lesson")
    require_status(lesson, {"ready"}, "approve")

    content = lesson["content"]
    if body.lesson is not None:
        content["lesson"] = body.lesson
    if body.questions is not None:
        content["worksheet"]["questions"] = [q.model_dump(exclude_none=True) for q in body.questions]
    if body.title:
        content["worksheet"]["title"] = body.title

    worksheet = content["worksheet"]
    worksheet_id = repo.create_worksheet(
        lesson["class_id"], worksheet["title"], lesson["subject"], lesson["topic"],
        worksheet["questions"], with_defaults(worksheet["misconceptions"]), lesson_id,
    )
    repo.update_lesson(lesson_id, content=content, status="approved", worksheet_id=worksheet_id)
    return {"lesson_id": lesson_id, "worksheet_id": worksheet_id}


@router.post("/lessons/{lesson_id}/retry", status_code=202)
def retry_lesson(lesson_id: int):
    lesson = found(repo.get_lesson(lesson_id), "Lesson")
    require_status(lesson, {"error"}, "retry")
    repo.update_lesson(lesson_id, status="queued", error=None)
    jobs.submit(jobs.run_lesson, lesson_id)
    return {"status": "queued"}


@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: int):
    """Deletes a lesson plan (not while it is still being written).

    Its worksheet is deleted too, unless student work was already checked on it.
    """
    lesson = found(repo.get_lesson(lesson_id), "Lesson")
    require_status(lesson, {"ready", "approved", "error"}, "delete")
    return repo.delete_lesson(lesson_id)
