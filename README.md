# Dgx_Hack

Simple FastAPI project for the SFBUxNVDIA hackathon.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest httpx
cp .env.example .env
```

Add your API key to `.env`, then start the API:

## Run

```bash
uvicorn app.main:app --reload
```

Health endpoints: `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/healthz`

Generate an essay:

```bash
curl -X POST http://127.0.0.1:8000/essay \
  -H "Content-Type: application/json" \
  -d '{"topic":"The future of artificial intelligence"}'
```

## Test

```bash
pytest -q
```
