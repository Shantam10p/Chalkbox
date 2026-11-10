from fastapi import APIRouter

from app.api import classes, followup, lessons, submissions, worksheets

router = APIRouter(prefix="/api")
for module in (classes, worksheets, submissions, lessons, followup):
    router.include_router(module.router)
