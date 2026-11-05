from fastapi import FastAPI

app = FastAPI(title="DGX Hack API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
