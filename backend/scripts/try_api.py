"""End-to-end test of the hub API, doing what the teacher app will do.

Needs a running server and seeded data:
    python -m scripts.seed --reset
    python -m uvicorn app.main:app --port 8000
    python -m scripts.try_api [--skip-lesson]
"""

import json
import sys
import tempfile
import time
from pathlib import Path

import httpx

from scripts.samples import ACCOUNTS, FRACTIONS_WORKSHEET, SAMPLE_ANSWERS, draw_worksheet

BASE = "http://127.0.0.1:8000/api"
DONE = {"graded", "needs_review", "ready", "approved", "error"}
client = httpx.Client(base_url=BASE, timeout=60)
started = time.perf_counter()


def log(message: str) -> None:
    print(f"[{time.perf_counter() - started:6.0f}s] {message}", flush=True)


def call(method: str, path: str, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {path} -> {response.status_code}: {response.text}")
    return response.json()


def wait(path: str, until=DONE, every: float = 5):
    while True:
        item = call("GET", path)
        if item["status"] in until:
            return item
        time.sleep(every)


def main() -> None:
    teacher = next(a for a in ACCOUNTS if a["role"] == "teacher")
    call("POST", "/auth/login", json={"username": teacher["username"], "password": teacher["password"]})
    log(f"Signed in as {teacher['username']}")

    class_ = call("GET", "/classes/1")
    worksheet_id = class_["worksheets"][0]["id"]
    log(f"Class {class_['name']} ({len(class_['students'])} students), worksheet {worksheet_id}")

    # 1. Upload two filled-in worksheets.
    all_correct = {q["number"]: q.get("answer", "") for q in FRACTIONS_WORKSHEET["questions"]}
    all_correct["7"] = "A"
    all_correct["8"] = "The bottom number stays the same, you only add the top numbers"
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for name, answers in (("Maya", SAMPLE_ANSWERS), ("Lucas", all_correct)):
            path = Path(tmp) / f"{name}.png"
            draw_worksheet(path, FRACTIONS_WORKSHEET, answers, name)
            files.append(("files", (path.name, path.read_bytes(), "image/png")))
        ids = call("POST", f"/worksheets/{worksheet_id}/submissions", files=files)["submission_ids"]
    log(f"Uploaded submissions {ids}")

    # 2. Wait for each one; answer the teacher review if the AI asks for one.
    for submission_id in ids:
        sub = wait(f"/submissions/{submission_id}")
        if sub["status"] == "needs_review":
            flagged = sub["review"]["flagged"]
            log(f"#{submission_id} needs review: {[(f['question'], f['read_as']) for f in flagged]}")
            call("POST", f"/submissions/{submission_id}/review", json={"corrections": {}})
            sub = wait(f"/submissions/{submission_id}", until={"graded", "error"})
        if sub["status"] == "error":
            raise SystemExit(f"#{submission_id} failed: {sub['error']}")
        log(f"#{submission_id} graded: read name {sub['student_name_read']!r} -> student "
            f"{sub['student_name']!r}, score {sub['score_correct']}/{sub['score_total']}")
        for a in sub["answers"]:
            log(f"    Q{a['question_no']} {a['correct']!s:5} [{a['graded_by']}] {a['student_answer']!r}"
                f" {a['misconception'] or ''} {a['explanation'] or ''}")
        log(f"    feedback: {sub['feedback']}")

        # 3. Teacher approves (student was matched automatically from the name).
        approved = call("POST", f"/submissions/{submission_id}/approve", json={})
        log(f"#{submission_id} approved for {approved['student_name']}")

    # 4. Class summary and a student profile.
    summary = call("GET", f"/worksheets/{worksheet_id}/summary")
    log("Summary: " + json.dumps({k: summary[k] for k in ("graded", "average", "top_mistakes", "groups")}))
    maya = next(s for s in class_["students"] if s["name"].startswith("Maya"))
    profile = call("GET", f"/students/{maya['id']}/profile")
    log(f"Maya's profile: trend {profile['trend']}, mistakes {profile['top_mistakes']}")

    # 5. Personalized practice sheets.
    practice_ids = call("POST", f"/worksheets/{worksheet_id}/practice", json={})["practice_ids"]
    for practice_id in practice_ids:
        sheet = wait(f"/practice/{practice_id}")
        log(f"Practice for {sheet['student_name']} [{sheet['status']}]: "
            f"{json.dumps(sheet['content'], ensure_ascii=False)} {sheet['error'] or ''}")

    # 6. Parent note for Maya, in her family language.
    report_id = call("POST", "/classes/1/reports", json={"student_ids": [maya["id"]]})["report_ids"][0]
    report = wait(f"/reports/{report_id}")
    log(f"Parent note ({report['language']}) [{report['status']}]: {report['text'] or report['error']}")

    # 7. Plan the next lesson.
    if "--skip-lesson" not in sys.argv:
        lesson_id = call("POST", "/lessons", json={
            "class_id": 1, "subject": "Math", "topic": "Subtracting fractions with the same denominator",
            "num_questions": 6,
        })["id"]
        lesson = wait(f"/lessons/{lesson_id}")
        if lesson["status"] == "error":
            log(f"Lesson failed: {lesson['error']}")
        else:
            content = lesson["content"]
            log("Lesson: " + json.dumps(content["lesson"], ensure_ascii=False))
            log("Worksheet: " + json.dumps(content["worksheet"]["questions"], ensure_ascii=False))
            log(f"Verifier notes: {content['problems']}")
            result = call("POST", f"/lessons/{lesson_id}/approve", json={})
            log(f"Lesson approved -> worksheet {result['worksheet_id']}")

    log("End-to-end test finished.")


if __name__ == "__main__":
    main()
