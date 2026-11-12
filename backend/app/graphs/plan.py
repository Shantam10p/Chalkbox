"""Graph 2: Plan a lesson and its worksheet.

    write_lesson ─► write_worksheet ─► verify ─┬─► END
                          ▲                    │
                          └── retry (once) ────┘  if no usable questions

- write_lesson:    text model writes the 5-part lesson (goal, explain the idea,
                   practice as a class, independent practice, teacher notes)
- write_worksheet: text model writes typed questions, answers/rubrics and a topic-specific
                   list of common mistakes
- verify:          plain code recomputes every arithmetic answer and drops broken questions

Teacher approval happens afterwards through the API (lesson status 'ready' -> 'approved').
"""

import string
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app import misconceptions as mc
from app.grading import QUESTION_TYPES, evaluate_expression, format_number, parse_number
from app.llm import ask_json

MAX_WORKSHEET_ATTEMPTS = 2


class PlanState(TypedDict, total=False):
    # Inputs
    subject: str
    topic: str
    grade: int
    minutes: int
    num_questions: int
    language: str
    # Outputs
    lesson: dict
    questions: list[dict]
    misconceptions: dict[str, str]
    problems: list[str]            # what verify had to fix or drop
    attempts: int


def _timing(minutes: int) -> dict[str, int]:
    total = max(minutes, 15)
    teach, together = round(total * 0.3), round(total * 0.25)
    return {"teach": teach, "practice_together": together, "practice_alone": total - teach - together}


def write_lesson(state: PlanState) -> dict:
    lesson = ask_json(
        "You help teachers in low-resource schools plan clear lessons that need only chalk, "
        "paper and everyday objects (no screens).",
        f"Plan a {state.get('minutes', 40)}-minute Grade {state['grade']} {state['subject']} "
        f"lesson on '{state['topic']}'. The class language is {state.get('language', 'English')}.\n\n"
        "Return JSON with exactly these keys:\n"
        '{"goal": "<one sentence: what students will be able to do>",\n'
        ' "teach": {"explanation": "...", "examples": ["...", "..."], "watch_for": ["common mistake", "..."]},\n'
        ' "practice_together": ["problem to solve with the class on the board", "..."],\n'
        ' "practice_alone": "<one sentence telling students what to do on the worksheet>",\n'
        ' "teacher_notes": {"materials": ["..."], "local_language_words": ["..."], "tips": ["..."]}}',
        temperature=0.4,
        max_tokens=2000,
    )
    if not isinstance(lesson, dict):
        lesson = {}
    lesson["timing"] = _timing(int(state.get("minutes", 40)))
    return {"lesson": lesson, "attempts": 0}


def write_worksheet(state: PlanState) -> dict:
    count = int(state.get("num_questions", 8))
    is_math = state["subject"].strip().lower() in {"math", "maths", "mathematics", "arithmetic"}
    mix = (
        "Most questions should be type 'number' (arithmetic with one exact answer, written "
        "like '3/8 + 1/8 ='). Include one 'choice' and one 'short_answer' question."
        if is_math else
        "Use a mix of 'choice', 'text' (one exact word) and 'short_answer' questions."
    )
    reply = ask_json(
        "You write clear, age-appropriate school worksheets with correct answer keys.",
        f"Write a worksheet of {count} questions for Grade {state['grade']} {state['subject']}: "
        f"'{state['topic']}'. Lesson goal: {state.get('lesson', {}).get('goal', '')}\n{mix}\n\n"
        "Question types:\n"
        "- number: needs \"answer\" (e.g. \"1/2\" or \"48\")\n"
        "- choice: needs \"options\" (e.g. [\"A. 1/4\", \"B. 1/8\"]) and \"answer\" (the letter)\n"
        "- text: needs \"answer\" (one word or short phrase)\n"
        "- short_answer: needs \"rubric\" (what a correct answer must mention)\n\n"
        "Also list 4-6 common mistakes students make on this topic, as short snake_case ids.\n\n"
        'Return JSON: {"questions": [{"number": "1", "text": "...", "type": "...", "answer": "...", '
        '"options": [...], "rubric": "..."}], "misconceptions": {"mistake_id": "description"}}',
        temperature=0.3,
        max_tokens=2000,
    )
    if not isinstance(reply, dict):
        reply = {}
    return {
        "questions": reply.get("questions") or [],
        "misconceptions": reply.get("misconceptions") or {},
        "attempts": state.get("attempts", 0) + 1,
    }


def verify(state: PlanState) -> dict:
    """Code checks the AI's worksheet: recompute arithmetic answers, drop broken questions."""
    verified: list[dict] = []
    problems: list[str] = []

    for raw in state.get("questions") or []:
        if not isinstance(raw, dict) or not str(raw.get("text") or "").strip():
            problems.append("Dropped a question with no text.")
            continue
        question = {
            "text": str(raw["text"]).strip(),
            "type": raw.get("type") if raw.get("type") in QUESTION_TYPES else "short_answer",
        }
        kind = question["type"]

        if kind == "number":
            computed = evaluate_expression(question["text"])
            given = parse_number(str(raw.get("answer") or ""))
            if computed is not None:
                if given is not None and given != computed:
                    problems.append(
                        f"Fixed the answer to '{question['text']}': AI said {raw.get('answer')}, "
                        f"correct is {format_number(computed)}."
                    )
                question["answer"] = format_number(computed)
                question["verified"] = True
            elif given is not None:
                question["answer"] = format_number(given)
                question["verified"] = False
                problems.append(f"Could not check '{question['text']}' automatically; please check it.")
            else:
                problems.append(f"Dropped '{question['text']}': no usable answer.")
                continue
        elif kind == "choice":
            options = [str(o) for o in raw.get("options") or []]
            letter = str(raw.get("answer") or "").strip().upper()[:1]
            if len(options) < 2 or letter not in string.ascii_uppercase[: len(options)]:
                problems.append(f"Dropped '{question['text']}': options or answer letter missing.")
                continue
            question.update(options=options, answer=letter)
        elif kind == "text":
            if not str(raw.get("answer") or "").strip():
                problems.append(f"Dropped '{question['text']}': no answer.")
                continue
            question["answer"] = str(raw["answer"]).strip()
        else:
            question["rubric"] = str(raw.get("rubric") or raw.get("answer") or "").strip()
            if not question["rubric"]:
                problems.append(f"'{question['text']}' has no marking guide; the AI will use judgement.")

        verified.append(question)

    for index, question in enumerate(verified, start=1):
        question["number"] = str(index)

    raw_mistakes = state.get("misconceptions")
    mistakes = {
        str(k).strip().lower().replace(" ", "_"): str(v)
        for k, v in (raw_mistakes.items() if isinstance(raw_mistakes, dict) else [])
    }
    return {"questions": verified, "misconceptions": mc.with_defaults(mistakes), "problems": problems}


def _after_verify(state: PlanState) -> str:
    if not state.get("questions") and state.get("attempts", 0) < MAX_WORKSHEET_ATTEMPTS:
        return "retry"
    return "done"


def build_plan_graph():
    graph = StateGraph(PlanState)
    graph.add_node("write_lesson", write_lesson)
    graph.add_node("write_worksheet", write_worksheet)
    graph.add_node("verify", verify)

    graph.add_edge(START, "write_lesson")
    graph.add_edge("write_lesson", "write_worksheet")
    graph.add_edge("write_worksheet", "verify")
    graph.add_conditional_edges("verify", _after_verify, {"retry": "write_worksheet", "done": END})
    return graph.compile()
