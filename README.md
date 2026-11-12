# ChalkBox

**Made for NVIDIA DGX Spark x SFBU hackathon**

AI hub for schools where the internet is a problem. One box in the school (an NVIDIA
DGX Spark in production) runs AI workflows that teachers use from their phones over the
school's local Wi-Fi: lesson planning, reading and grading handwritten worksheets,
per-student feedback, personalized practice, and parent reports.

```
backend/    FastAPI hub, AI workflows, database (Python)
frontend/   teacher app (React)
```

## Setup (Windows)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Pick a model preset in `backend\.env`:

- **A. Ollama (offline, default):** `ollama pull qwen2.5vl:3b` and `ollama pull qwen3:4b-instruct` (use instruct models: thinking models are far too slow)
- **B. NVIDIA API catalog:** add your `nvapi-...` key and model ids from build.nvidia.com
- **C. DGX Spark:** point the URLs at the vLLM / NIM server on the Spark, and raise `WORKERS`

## Run

Every backend command runs from the `backend` folder:

```powershell
cd backend
.venv\Scripts\python -m scripts.check_models     # both models answer?
.venv\Scripts\python -m scripts.seed --reset     # demo class: Grade 4A, Dave, 30 students
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- On this machine: http://localhost:8000 (API docs at http://localhost:8000/docs)
- From a phone on the same Wi-Fi: `http://<this-computer's-IP>:8000`
  (allow Python through Windows Firewall when asked)

### Teacher app (React)

```powershell
cd frontend
npm install
npm run dev      # development: http://localhost:5173, API calls are forwarded to :8000
npm run build    # production: writes frontend/dist, which the hub serves at :8000
```

After `npm run build`, restart the hub and the whole app (UI + API) runs from one
address, so phones on the school Wi-Fi only need `http://<hub-IP>:8000`.

Test scripts (from `backend`, server running, data seeded):

```powershell
.venv\Scripts\python -m scripts.try_check        # Check graph only, no server needed
.venv\Scripts\python -m scripts.try_api          # full teacher flow through the API
```

## Accounts

The seed script creates two demo logins (`python -m scripts.seed` adds them to an
existing database without touching other data):

| Username | Password | Role | Can see |
|---|---|---|---|
| `dave` | `dave123` | Teacher | Everything: planning, checking, class results, reports |
| `maya` | `maya123` | Student (Maya Johnson) | Her own approved work and feedback, her practice sheets, her progress, and the Ask helper |

Change these passwords before using ChalkBox with a real class. Passwords are stored as
PBKDF2 hashes; the browser keeps a 30-day HttpOnly session cookie. Students only ever see
work the teacher has approved, and practice sheets without the answers.

The student **Ask** helper only discusses topics from the class's worksheets and lessons, gives
hints instead of answers, declines anything off-topic, flags worrying messages for the
teacher, and allows 30 questions per hour. Teachers can read every chat on the student's profile.

## How it works

Three LangGraph workflows. Code does everything that must be exact; models do reading,
judging open answers, and writing. The teacher approves everything.

| Graph | Steps |
|---|---|
| **Check** (one worksheet photo) | read (vision) → mark (code) → ⏸ teacher fixes unsure readings → AI-grade open answers → diagnose mistakes + feedback |
| **Plan** (lesson) | write 5-part lesson → write typed worksheet + topic mistakes → verify answers in code (retry once) |
| **Follow-up** (one student) | practice sheet → verify answers in code, *or* parent note in the family's language |

Question types: `number` (incl. fractions), `choice`, `text` are graded by code;
`short_answer` is graded by the AI against a rubric.

AI work runs in background jobs (`WORKERS` at a time). Every item has a `status`:

- submissions: `queued → reading → needs_review → grading → graded → approved` (or `error`)
- lessons, practice sheets, reports: `queued → running → ready → approved` (or `error`)

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | configured models, worker count |
| GET/POST | `/api/classes` | list / create classes |
| GET | `/api/classes/{id}` | class with students, worksheets, lessons |
| POST | `/api/classes/{id}/students` | add a student |
| GET | `/api/students/{id}/profile` | scores over time, trend, top mistakes |
| POST | `/api/worksheets` | create a worksheet (typed questions + answers) |
| GET | `/api/worksheets?class_id=` · `/api/worksheets/{id}` | list / get |
| POST | `/api/worksheets/{id}/submissions` | upload photos (multipart `files`) → starts Check |
| GET | `/api/worksheets/{id}/submissions` | all submissions + statuses |
| GET | `/api/worksheets/{id}/summary` | class view: accuracy per question, top mistakes, groups |
| GET | `/api/submissions/{id}` · `/image` | result with answers · the photo |
| POST | `/api/submissions/{id}/review` | ⏸ `{"corrections": {"4": "3/8"}}` resumes the graph |
| POST | `/api/submissions/{id}/approve` | `{"student_id"?, "overrides"?: {"8": true}, "feedback"?}` |
| POST | `/api/submissions/{id}/retry` | re-run a failed check |
| POST | `/api/lessons` | `{"class_id", "subject", "topic", "minutes"?, "num_questions"?}` → starts Plan |
| GET | `/api/lessons?class_id=` · `/api/lessons/{id}` | list / get |
| POST | `/api/lessons/{id}/approve` | optional edits → creates the gradable worksheet |
| POST | `/api/worksheets/{id}/practice` | practice sheet per student with graded work |
| GET | `/api/worksheets/{id}/practice` · `/api/practice/{id}` | list / get |
| POST | `/api/practice/{id}/approve` | optional edits |
| POST | `/api/classes/{id}/reports` | parent note per student (family language) |
| GET | `/api/classes/{id}/reports` · `/api/reports/{id}` | list / get |
| POST | `/api/reports/{id}/approve` | optional edited text |

## Layout

```
backend/
 app/
  main.py           FastAPI hub + serves the web app
  config.py         settings from .env (model endpoints, data folder, workers)
  llm.py            one OpenAI-compatible client for every model
  db.py             SQLite schema
  repo.py           database helpers
  analysis.py       class summary, student profiles (plain code)
  grading.py        exact grading + arithmetic checker (plain code)
  misconceptions.py mistake lists (fractions + general)
  jobs.py           background runner for the graphs
  schemas.py        API request bodies
  api/              API routes
  graphs/           check.py, plan.py, followup.py (LangGraph)
  static/           placeholder page (used until the React app is built)
 scripts/           check_models, seed, try_check, try_api, samples
 data/              local database + uploaded photos (gitignored)
 requirements.txt   Python dependencies
 .env.example       model settings template (copy to .env)
frontend/           React teacher app (Vite); src/api.js wraps every API call
```
