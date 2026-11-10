from fastapi import APIRouter, HTTPException

from app import jobs, repo
from app.api.common import found, require_status
from app.schemas import ApprovePracticeIn, ApproveReportIn, PracticeIn, ReportsIn

router = APIRouter(tags=["follow-up"])


def _students_with_graded_work(worksheet_id: int) -> list[int]:
    return sorted({
        s["student_id"] for s in repo.list_submissions(worksheet_id)
        if s["student_id"] is not None and s["status"] in ("graded", "approved")
    })


# ---------------------------------------------------------------- practice sheets

@router.post("/worksheets/{worksheet_id}/practice", status_code=202)
def create_practice(worksheet_id: int, body: PracticeIn):
    """Starts one personalized practice sheet per student, based on their own mistakes."""
    found(repo.get_worksheet(worksheet_id), "Worksheet")
    student_ids = body.student_ids or _students_with_graded_work(worksheet_id)
    if not student_ids:
        raise HTTPException(status_code=400, detail="No graded worksheets linked to students yet")
    created = []
    for student_id in student_ids:
        found(repo.get_student(student_id), "Student")
        practice_id = repo.create_practice(worksheet_id, student_id)
        jobs.submit(jobs.run_practice, practice_id, body.num_questions)
        created.append(practice_id)
    return {"practice_ids": created}


@router.get("/worksheets/{worksheet_id}/practice")
def list_practice(worksheet_id: int):
    return repo.list_practice(worksheet_id)


@router.get("/practice/{practice_id}")
def get_practice(practice_id: int):
    return found(repo.get_practice(practice_id), "Practice sheet")


@router.post("/practice/{practice_id}/approve")
def approve_practice(practice_id: int, body: ApprovePracticeIn):
    practice = found(repo.get_practice(practice_id), "Practice sheet")
    require_status(practice, {"ready", "approved"}, "approve")
    content = practice["content"] or {}
    if body.intro is not None:
        content["intro"] = body.intro
    if body.questions is not None:
        content["questions"] = body.questions
    repo.update_practice(practice_id, content=content, status="approved")
    return repo.get_practice(practice_id)


# ---------------------------------------------------------------- parent reports

@router.post("/classes/{class_id}/reports", status_code=202)
def create_reports(class_id: int, body: ReportsIn):
    """Starts a parent note per student, written in each family's language."""
    found(repo.get_class(class_id), "Class")
    students = {s["id"]: s for s in repo.list_students(class_id)}
    if body.student_ids:
        student_ids = body.student_ids
    else:
        graded = {sid for ws in repo.list_worksheets(class_id) for sid in _students_with_graded_work(ws["id"])}
        student_ids = sorted(graded)
    if not student_ids:
        raise HTTPException(status_code=400, detail="No graded work linked to students yet")

    created = []
    for student_id in student_ids:
        student = students.get(student_id)
        if student is None:
            raise HTTPException(status_code=404, detail=f"Student {student_id} is not in this class")
        report_id = repo.create_report(class_id, student_id, body.language or student["language"])
        jobs.submit(jobs.run_report, report_id)
        created.append(report_id)
    return {"report_ids": created}


@router.get("/classes/{class_id}/reports")
def list_reports(class_id: int):
    return repo.list_reports(class_id)


@router.get("/reports/{report_id}")
def get_report(report_id: int):
    return found(repo.get_report(report_id), "Report")


@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, body: ApproveReportIn):
    report = found(repo.get_report(report_id), "Report")
    require_status(report, {"ready", "approved"}, "approve")
    fields = {"status": "approved"}
    if body.text is not None:
        fields["text"] = body.text
    repo.update_report(report_id, **fields)
    return repo.get_report(report_id)
