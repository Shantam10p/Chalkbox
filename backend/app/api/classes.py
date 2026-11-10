from fastapi import APIRouter

from app import analysis, repo
from app.api.common import found
from app.schemas import ClassIn, StudentIn

router = APIRouter(tags=["classes"])


@router.get("/classes")
def list_classes():
    return repo.list_classes()


@router.post("/classes", status_code=201)
def create_class(body: ClassIn):
    return {"id": repo.create_class(body.name, body.grade, body.teacher)}


@router.get("/classes/{class_id}")
def get_class(class_id: int):
    class_ = found(repo.get_class(class_id), "Class")
    return {
        **class_,
        "students": repo.list_students(class_id),
        "worksheets": repo.list_worksheets(class_id),
        "lessons": repo.list_lessons(class_id),
    }


@router.post("/classes/{class_id}/students", status_code=201)
def add_student(class_id: int, body: StudentIn):
    found(repo.get_class(class_id), "Class")
    return {"id": repo.add_student(class_id, body.name, body.language)}


@router.get("/students/{student_id}/profile")
def student_profile(student_id: int):
    return found(analysis.student_profile(student_id), "Student")
