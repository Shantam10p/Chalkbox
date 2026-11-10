# ChalkBox

AI hub for schools where the internet is a problem. One box in the school (an NVIDIA
DGX Spark in production) runs a team of AI agents that teachers use from their phones
over the school's local Wi-Fi: lesson planning, reading and grading handwritten
worksheets, per-student feedback, personalized practice, and parent reports.

## Setup (Windows)

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Pick a model preset in `.env`:

- **A. Ollama (offline, default):** `ollama pull qwen2.5vl:3b` and `ollama pull qwen3:4b`
- **B. NVIDIA API catalog:** add your `nvapi-...` key and model ids from build.nvidia.com
- **C. DGX Spark:** point the URLs at the vLLM / NIM server on the Spark

## Check the models

```powershell
.venv\Scripts\python -m scripts.check_models
```

## Run the hub

```powershell
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- On this machine: http://localhost:8000
- From a phone on the same Wi-Fi: `http://<this-computer's-IP>:8000`
  (allow Python through Windows Firewall when asked)
- `GET /health` and `GET /api/status` show the hub is up and which models it uses

## Layout

```
app/
  main.py      FastAPI hub + serves the web app
  config.py    settings from .env (model endpoints, data folder)
  llm.py       one OpenAI-compatible client for every model
  db.py        SQLite schema (classes, students, lessons, worksheets, submissions, answers)
  agents/      Reader, Checker, Diagnoser, Planner, Coach, Reporter, Boss
  static/      teacher web app
scripts/
  check_models.py   smoke test for the configured models
data/          local database + uploaded photos (gitignored)
```
