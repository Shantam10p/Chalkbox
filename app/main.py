from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.essay_agent import write_essay

app = FastAPI(title="DGX Hack API")


class EssayRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)


class EssayResponse(BaseModel):
    topic: str
    essay: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/essay", response_model=EssayResponse)
def generate_essay(request: EssayRequest):
    try:
        essay = write_essay(request.topic)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return EssayResponse(topic=request.topic, essay=essay)
