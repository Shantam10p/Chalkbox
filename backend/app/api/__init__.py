from fastapi import APIRouter, Depends

from app.api import auth, classes, followup, lessons, student, submissions, worksheets
from app.auth import require_teacher

router = APIRouter(prefix="/api")

# Sign in / out: open to everyone.
router.include_router(auth.router)

# Everything the teacher app uses: teacher accounts only.
for module in (classes, worksheets, submissions, lessons, followup):
    router.include_router(module.router, dependencies=[Depends(require_teacher)])

# A student's own approved work: student accounts only (checked inside each route).
router.include_router(student.router)
