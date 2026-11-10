"""Request bodies for the API."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Question(BaseModel):
    number: str
    text: str = Field(min_length=1)
    type: Literal["number", "choice", "text", "short_answer"]
    answer: str | None = None            # number / choice letter / text
    options: list[str] | None = None     # choice only
    accept: list[str] | None = None      # text only: other accepted spellings
    simplify: bool = False               # number only: require simplest form
    rubric: str | None = None            # short_answer only: what a correct answer mentions

    @model_validator(mode="after")
    def check_fields(self):
        if self.type != "short_answer" and not (self.answer or "").strip():
            raise ValueError(f"Question {self.number}: '{self.type}' questions need an answer")
        if self.type == "choice" and len(self.options or []) < 2:
            raise ValueError(f"Question {self.number}: choice questions need at least 2 options")
        return self


class ClassIn(BaseModel):
    name: str = Field(min_length=1)
    grade: int = Field(ge=1, le=12)
    teacher: str | None = None


class StudentIn(BaseModel):
    name: str = Field(min_length=1)
    language: str = "English"


class WorksheetIn(BaseModel):
    class_id: int
    title: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    questions: list[Question] = Field(min_length=1)
    misconceptions: dict[str, str] | None = None


class ReviewIn(BaseModel):
    corrections: dict[str, str] = {}     # {question_number: what the student actually wrote}


class ApproveSubmissionIn(BaseModel):
    student_id: int | None = None
    overrides: dict[str, bool] = {}      # {question_number: correct?}
    feedback: str | None = None


class LessonIn(BaseModel):
    class_id: int
    subject: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    title: str | None = None
    minutes: int = Field(default=40, ge=15, le=120)
    num_questions: int = Field(default=8, ge=2, le=20)
    language: str | None = None
    fix_yesterday: bool = True


class ApproveLessonIn(BaseModel):
    lesson: dict | None = None           # edited lesson parts, if the teacher changed them
    questions: list[Question] | None = None
    title: str | None = None


class PracticeIn(BaseModel):
    student_ids: list[int] | None = None  # default: every student with graded work
    num_questions: int = Field(default=4, ge=2, le=10)


class ApprovePracticeIn(BaseModel):
    intro: str | None = None
    questions: list[dict] | None = None


class ReportsIn(BaseModel):
    student_ids: list[int] | None = None  # default: every student with graded work
    language: str | None = None           # default: each student's family language


class ApproveReportIn(BaseModel):
    text: str | None = None
