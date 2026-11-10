from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app import jobs, repo
from app.api.common import found, require_status
from app.config import settings
from app.schemas import ApproveSubmissionIn, ReviewIn

router = APIRouter(tags=["submissions"])


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: int):
    return found(repo.get_submission(submission_id), "Submission")


@router.get("/submissions/{submission_id}/image")
def submission_image(submission_id: int):
    submission = found(repo.get_submission(submission_id), "Submission")
    path = settings.data_path(submission["image_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo file is missing")
    return FileResponse(path, media_type="image/jpeg")


@router.post("/submissions/{submission_id}/review", status_code=202)
def review_submission(submission_id: int, body: ReviewIn):
    """Teacher checkpoint 1: confirm or correct the answers the AI wasn't sure it read right."""
    submission = found(repo.get_submission(submission_id), "Submission")
    require_status(submission, {"needs_review"}, "submit a review")
    repo.update_submission(submission_id, status="grading", review=None)
    jobs.submit(jobs.run_check, submission_id, body.corrections)
    return {"status": "grading"}


@router.post("/submissions/{submission_id}/approve")
def approve_submission(submission_id: int, body: ApproveSubmissionIn):
    """Teacher checkpoint 2: sign off the marks and feedback (with optional changes)."""
    submission = found(repo.get_submission(submission_id), "Submission")
    require_status(submission, {"graded", "approved"}, "approve")
    student_id = body.student_id if body.student_id is not None else submission["student_id"]
    if student_id is None:
        raise HTTPException(status_code=400, detail="Pick which student this worksheet belongs to")
    found(repo.get_student(student_id), "Student")
    repo.approve_submission(submission_id, student_id, body.overrides, body.feedback)
    return repo.get_submission(submission_id)


@router.post("/submissions/{submission_id}/retry", status_code=202)
def retry_submission(submission_id: int):
    submission = found(repo.get_submission(submission_id), "Submission")
    require_status(submission, {"error"}, "retry")
    repo.update_submission(submission_id, thread_id=jobs.new_thread_id(submission_id),
                           status="queued", error=None)
    jobs.submit(jobs.run_check, submission_id)
    return {"status": "queued"}
