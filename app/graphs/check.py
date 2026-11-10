"""Graph 1: Check one student's worksheet.

    read ──► mark ──┬──► review (⏸ teacher fixes flagged readings) ──► mark
                    └──► diagnose (why wrong + feedback) ──► END

- read:     vision model copies the student's name and answers from the photo
- mark:     plain code grades every answer against the key (exact, never an AI guess)
- review:   pauses the graph until the teacher confirms or corrects low-confidence readings
- diagnose: text model tags each mistake and writes short feedback for the student
"""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app import misconceptions
from app.grading import grade_answer
from app.llm import ask_json, ask_vision_json

# Readings below this confidence are sent to the teacher.
CONFIDENCE_THRESHOLD = 0.7


class QuestionResult(TypedDict, total=False):
    answer: str
    working: str
    confidence: float
    teacher_fixed: bool
    correct: bool | None
    misconception: str | None
    explanation: str


class CheckState(TypedDict, total=False):
    # Inputs
    image_path: str
    questions: dict[str, str]      # {"1": "1/4 + 1/4"}
    answer_key: dict[str, Any]     # {"1": "1/2"} or {"1": {"answer": "1/2", "simplify": True}}
    # Outputs
    student_name: str
    results: dict[str, QuestionResult]
    flagged: list[str]
    score: str
    feedback: str


def _key_entry(entry: Any) -> tuple[str, bool]:
    if isinstance(entry, dict):
        return str(entry["answer"]), bool(entry.get("simplify", False))
    return str(entry), False


# ---------------------------------------------------------------- nodes

def read(state: CheckState) -> dict:
    numbers = list(state["answer_key"].keys())
    example = {n: {"answer": "...", "working": "...", "confidence": 0.9} for n in numbers[:2]}
    reply = ask_vision_json(
        "You read photos of handwritten Grade 4 math worksheets. Copy exactly what the "
        "student wrote. Never correct, solve, or improve any answer.",
        f"The worksheet has questions numbered {', '.join(numbers)}.\n"
        'Return JSON: {"name": "<student name, or empty>", "answers": {<question number>: '
        '{"answer": "<exactly as written, e.g. 3/8>", "working": "<working shown, or empty>", '
        '"confidence": <0 to 1, how sure you are you read it correctly>}}}\n'
        f"Example shape: {example}\n"
        "Use an empty answer for a blank box. If you cannot read something, give your best "
        "guess with a low confidence.",
        state["image_path"],
    )

    raw_answers = reply.get("answers", {}) if isinstance(reply, dict) else {}
    results: dict[str, QuestionResult] = {}
    for number in numbers:
        item = raw_answers.get(number) or raw_answers.get(int(number) if number.isdigit() else number) or {}
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
    results = {n: dict(r) for n, r in state["results"].items()}
    flagged: list[str] = []
    correct_count = 0

    for number, entry in state["answer_key"].items():
        key_answer, simplify = _key_entry(entry)
        result = results[number]
        correct, code_misconception = grade_answer(result["answer"], key_answer, simplify)
        result["correct"] = correct
        result["misconception"] = code_misconception
        correct_count += bool(correct)

        unsure = result["confidence"] < CONFIDENCE_THRESHOLD or correct is None
        if unsure and not result.get("teacher_fixed"):
            flagged.append(number)

    return {
        "results": results,
        "flagged": flagged,
        "score": f"{correct_count}/{len(state['answer_key'])}",
    }


def review(state: CheckState) -> dict:
    """Pauses for the teacher. Resume with {question_number: corrected_answer}.

    Any flagged question the teacher leaves out is accepted as read.
    """
    corrections = interrupt(
        {
            "type": "review_readings",
            "student_name": state.get("student_name", ""),
            "image_path": state["image_path"],
            "flagged": [
                {
                    "question": n,
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
    return {"results": results}


def diagnose(state: CheckState) -> dict:
    results = {n: dict(r) for n, r in state["results"].items()}
    questions = state.get("questions", {})
    wrong = {
        n: r for n, r in results.items()
        if r.get("correct") is False and r["answer"] and not r.get("misconception")
    }

    for number, result in results.items():
        if result.get("misconception") == "not_simplified":
            result["explanation"] = "Your answer is right, but write it in its simplest form."

    if not wrong:
        missed = [n for n, r in results.items() if r.get("correct") is not True]
        feedback = (
            "Excellent work, everything is correct!"
            if not missed
            else f"Good work! Please look again at question(s) {', '.join(missed)}."
        )
        return {"results": results, "feedback": feedback}

    details = "\n".join(
        f"Q{n}: question '{questions.get(n, '?')}', correct answer "
        f"'{_key_entry(state['answer_key'][n])[0]}', student wrote '{r['answer']}'"
        + (f", working: '{r['working']}'" if r["working"] else "")
        for n, r in wrong.items()
    )
    reply = ask_json(
        "You are a kind Grade 4 math teacher's assistant. You find the reason behind each "
        "mistake and write feedback a 9-year-old can understand.",
        f"Possible mistake types:\n{misconceptions.describe_all()}\n\n"
        f"The student's wrong answers:\n{details}\n\n"
        "Return JSON: {\"diagnoses\": {<question number>: {\"misconception\": <one type id "
        "from the list>, \"explanation\": <one short sentence to the student about this "
        "question>}}, \"feedback\": <2-4 short, encouraging sentences to the student>}",
    )

    diagnoses = reply.get("diagnoses", {}) if isinstance(reply, dict) else {}
    for number in wrong:
        item = diagnoses.get(number) or diagnoses.get(f"Q{number}") or {}
        if not isinstance(item, dict):
            item = {}
        results[number]["misconception"] = misconceptions.normalize(item.get("misconception"))
        results[number]["explanation"] = str(item.get("explanation") or "").strip()

    feedback = str(reply.get("feedback") or "").strip() if isinstance(reply, dict) else ""
    return {"results": results, "feedback": feedback}


# ---------------------------------------------------------------- graph

def _after_mark(state: CheckState) -> str:
    return "review" if state.get("flagged") else "diagnose"


def build_check_graph(checkpointer=None):
    graph = StateGraph(CheckState)
    graph.add_node("read", read)
    graph.add_node("mark", mark)
    graph.add_node("review", review)
    graph.add_node("diagnose", diagnose)

    graph.add_edge(START, "read")
    graph.add_edge("read", "mark")
    graph.add_conditional_edges("mark", _after_mark, {"review": "review", "diagnose": "diagnose"})
    graph.add_edge("review", "mark")
    graph.add_edge("diagnose", END)
    return graph.compile(checkpointer=checkpointer)
