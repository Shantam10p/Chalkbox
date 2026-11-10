"""Graph 1: Check one student's worksheet.

    read ─► mark ─┬─► review (⏸ teacher fixes flagged readings) ─► mark
                  └─► ai_grade (open questions only) ─► diagnose ─► END

- read:     vision model copies the student's name and answers from the photo
- mark:     plain code grades every question that has one exact answer
- review:   pauses until the teacher confirms or corrects low-confidence readings
- ai_grade: text model judges open questions (short answers) against their rubric
- diagnose: text model tags each mistake and writes short feedback for the student
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app import misconceptions as mc
from app.grading import grade_question
from app.llm import ask_json, ask_vision_json

# Readings below this confidence are sent to the teacher.
CONFIDENCE_THRESHOLD = 0.7


class CheckState(TypedDict, total=False):
    # Inputs
    image_path: str
    questions: list[dict]          # worksheet questions, each with number/type/answer/...
    misconceptions: dict[str, str]
    # Outputs
    student_name: str
    results: dict[str, dict]       # per question: answer, working, confidence, correct, ...
    flagged: list[str]
    score_correct: int
    score_total: int
    feedback: str


def _by_number(state: CheckState) -> dict[str, dict]:
    return {str(q["number"]): q for q in state["questions"]}


def _lookup(mapping: dict, number: str):
    if not isinstance(mapping, dict):
        return None
    return mapping.get(number) or mapping.get(f"Q{number}") or mapping.get(f"q{number}")


def _describe_for_reading(question: dict) -> str:
    line = f"Q{question['number']}: {question['text']}"
    if question.get("type") == "choice":
        line += f"  (options: {'; '.join(question.get('options') or [])}; copy the letter chosen)"
    elif question.get("type") == "short_answer":
        line += "  (copy the full written sentence)"
    return line


# ---------------------------------------------------------------- nodes

def read(state: CheckState) -> dict:
    questions = state["questions"]
    reply = ask_vision_json(
        "You read photos of handwritten school worksheets. Copy exactly what the student "
        "wrote. Never correct, solve, or improve any answer.",
        "The worksheet questions are:\n"
        + "\n".join(_describe_for_reading(q) for q in questions)
        + '\n\nReturn JSON: {"name": "<student name, or empty>", "answers": {"<question number>": '
        '{"answer": "<exactly as written>", "working": "<working shown, or empty>", '
        '"confidence": <0 to 1, how sure you are you read it correctly>}}}\n'
        'Use the plain question number as the key, e.g. "1". Use an empty answer for a '
        "blank box. If you cannot read something, give your best guess with low confidence.",
        state["image_path"],
    )

    raw_answers = reply.get("answers", {}) if isinstance(reply, dict) else {}
    results: dict[str, dict] = {}
    for question in questions:
        number = str(question["number"])
        item = _lookup(raw_answers, number) or {}
        if not isinstance(item, dict):
            item = {"answer": str(item)}
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5
        results[number] = {
            "answer": str(item.get("answer") or "").strip(),
            "working": str(item.get("working") or "").strip(),
            "confidence": confidence,
            "teacher_fixed": False,
        }
    name = str(reply.get("name") or "").strip() if isinstance(reply, dict) else ""
    return {"student_name": name, "results": results}


def mark(state: CheckState) -> dict:
    questions = _by_number(state)
    results = {n: dict(r) for n, r in state["results"].items()}
    flagged: list[str] = []

    for number, question in questions.items():
        result = results[number]
        result.update(grade_question(question, result["answer"]))
        result["explanation"] = "No answer written." if not result["answer"] else ""

        unreadable = result["graded_by"] == "code" and result["correct"] is None
        unsure = result["confidence"] < CONFIDENCE_THRESHOLD or unreadable
        if unsure and not result.get("teacher_fixed"):
            flagged.append(number)

    return {"results": results, "flagged": flagged}


def review(state: CheckState) -> dict:
    """Pauses for the teacher. Resume with {question_number: corrected_answer}.

    Any flagged question the teacher leaves out is accepted as read.
    """
    corrections = interrupt(
        {
            "type": "review_readings",
            "student_name": state.get("student_name", ""),
            "flagged": [
                {
                    "question": n,
                    "text": _by_number(state)[n]["text"],
                    "read_as": state["results"][n]["answer"],
                    "confidence": state["results"][n]["confidence"],
                }
                for n in state["flagged"]
            ],
        }
    ) or {}

    results = {n: dict(r) for n, r in state["results"].items()}
    for number in state["flagged"]:
        if number in corrections:
            results[number]["answer"] = str(corrections[number]).strip()
        results[number]["confidence"] = 1.0
        results[number]["teacher_fixed"] = True
    return {"results": results, "flagged": []}


def ai_grade(state: CheckState) -> dict:
    questions = _by_number(state)
    results = {n: dict(r) for n, r in state["results"].items()}
    pending = [n for n, r in results.items() if r.get("graded_by") == "ai_pending"]
    if not pending:
        return {}

    details = "\n".join(
        f"Q{n}: question '{questions[n]['text']}'. Marking guide: "
        f"'{questions[n].get('rubric') or questions[n].get('answer') or 'use your judgement'}'. "
        f"Student wrote: '{results[n]['answer']}'"
        for n in pending
    )
    reply = ask_json(
        "You are a fair, kind school teacher's assistant marking short written answers. "
        "Accept answers that show the right idea even with spelling mistakes or simple words.",
        f"{details}\n\nReturn JSON: {{\"grades\": {{\"<question number>\": "
        "{\"correct\": true or false, \"reason\": \"<one short sentence>\"}}}}",
        temperature=0.0,
    )

    grades = reply.get("grades", {}) if isinstance(reply, dict) else {}
    for number in pending:
        item = _lookup(grades, number) or {}
        verdict = item.get("correct") if isinstance(item, dict) else None
        results[number]["correct"] = verdict if isinstance(verdict, bool) else None
        results[number]["graded_by"] = "ai"
        if isinstance(item, dict) and item.get("reason"):
            results[number]["explanation"] = str(item["reason"]).strip()
    return {"results": results}


def diagnose(state: CheckState) -> dict:
    questions = _by_number(state)
    allowed = mc.with_defaults(state.get("misconceptions"))
    results = {n: dict(r) for n, r in state["results"].items()}

    for result in results.values():
        if result.get("misconception") == "not_simplified":
            result["explanation"] = "Your answer is right, but write it in its simplest form."

    wrong = {
        n: r for n, r in results.items()
        if r.get("correct") is False and r["answer"] and not r.get("misconception")
    }
    score_correct = sum(1 for r in results.values() if r.get("correct") is True)
    score = {"score_correct": score_correct, "score_total": len(results)}

    if not wrong:
        missed = [n for n, r in results.items() if r.get("correct") is not True]
        feedback = (
            "Excellent work, everything is correct!"
            if not missed
            else f"Good work! Please look again at question(s) {', '.join(missed)}."
        )
        return {"results": results, "feedback": feedback, **score}

    details = "\n".join(
        f"Q{n}: question '{questions[n]['text']}', expected "
        f"'{questions[n].get('answer') or questions[n].get('rubric') or '?'}', "
        f"student wrote '{r['answer']}'" + (f", working: '{r['working']}'" if r["working"] else "")
        for n, r in wrong.items()
    )
    reply = ask_json(
        "You are a kind school teacher's assistant. You find the reason behind each mistake "
        "and write feedback a 9-year-old can understand.",
        f"Possible mistake types:\n{mc.describe(allowed)}\n\n"
        f"The student's wrong answers:\n{details}\n\n"
        "Return JSON: {\"diagnoses\": {\"<question number>\": {\"misconception\": \"<one type "
        "id from the list>\", \"explanation\": \"<one short sentence to the student about "
        "this question>\"}}, \"feedback\": \"<2-4 short, encouraging sentences to the student>\"}",
        temperature=0.0,
    )

    diagnoses = reply.get("diagnoses", {}) if isinstance(reply, dict) else {}
    for number in wrong:
        item = _lookup(diagnoses, number)
        item = item if isinstance(item, dict) else {}
        results[number]["misconception"] = mc.normalize(item.get("misconception"), allowed)
        if item.get("explanation"):
            results[number]["explanation"] = str(item["explanation"]).strip()

    feedback = str(reply.get("feedback") or "").strip() if isinstance(reply, dict) else ""
    return {"results": results, "feedback": feedback, **score}


# ---------------------------------------------------------------- graph

def _after_mark(state: CheckState) -> str:
    return "review" if state.get("flagged") else "ai_grade"


def build_check_graph(checkpointer=None):
    graph = StateGraph(CheckState)
    graph.add_node("read", read)
    graph.add_node("mark", mark)
    graph.add_node("review", review)
    graph.add_node("ai_grade", ai_grade)
    graph.add_node("diagnose", diagnose)

    graph.add_edge(START, "read")
    graph.add_edge("read", "mark")
    graph.add_conditional_edges("mark", _after_mark, {"review": "review", "ai_grade": "ai_grade"})
    graph.add_edge("review", "mark")
    graph.add_edge("ai_grade", "diagnose")
    graph.add_edge("diagnose", END)
    return graph.compile(checkpointer=checkpointer)
