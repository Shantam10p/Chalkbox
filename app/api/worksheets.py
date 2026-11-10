import io
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app import analysis, jobs, repo
from app.api.common import found
from app.config import settings
from app.misconceptions import with_defaults
from app.schemas import WorksheetIn

router = APIRouter(tags=["worksheets"])

# Phone photos are shrunk before reading: much faster for the vision model, still legible.
MAX_PHOTO_SIDE = 1600


@router.post("/worksheets", status_code=201)
def create_worksheet(body: WorksheetIn):
    found(repo.get_class(body.class_id), "Class")
    worksheet_id = repo.create_worksheet(
        body.class_id, body.title, body.subject, body.topic,
        [q.model_dump(exclude_none=True) for q in body.questions],
        with_defaults(body.misconceptions),
    )
    return {"id": worksheet_id}


@router.get("/worksheets")
def list_worksheets(class_id: int | None = None):
    return repo.list_worksheets(class_id)


@router.get("/worksheets/{worksheet_id}")
def get_worksheet(worksheet_id: int):
    return found(repo.get_worksheet(worksheet_id), "Worksheet")


@router.get("/worksheets/{worksheet_id}/summary")
def worksheet_summary(worksheet_id: int):
    return found(analysis.worksheet_summary(worksheet_id), "Worksheet")


def _save_photo(data: bytes, filename: str) -> str:
    try:
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image).convert("RGB")  # fix phone rotation
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail=f"'{filename}' is not a readable image") from error
    image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
    path = settings.uploads_dir / f"{uuid.uuid4().hex}.jpg"
    image.save(path, "JPEG", quality=90)
    return str(path)


@router.post("/worksheets/{worksheet_id}/submissions", status_code=202)
async def upload_submissions(worksheet_id: int, files: list[UploadFile] = File(...)):
    """Upload one or more worksheet photos. Each one is checked in the background."""
    found(repo.get_worksheet(worksheet_id), "Worksheet")
    photos = [(await f.read(), f.filename or "photo") for f in files]
    paths = [_save_photo(data, name) for data, name in photos]  # validate all before queueing

    created = []
    for path in paths:
        submission_id = repo.create_submission(worksheet_id, path)
        repo.update_submission(submission_id, thread_id=jobs.new_thread_id(submission_id))
        jobs.submit(jobs.run_check, submission_id)
        created.append(submission_id)
    return {"submission_ids": created}


@router.get("/worksheets/{worksheet_id}/submissions")
def list_submissions(worksheet_id: int):
    found(repo.get_worksheet(worksheet_id), "Worksheet")
    return repo.list_submissions(worksheet_id)
