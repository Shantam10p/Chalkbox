"""Graph 3: Follow-up documents for one student.

    START ─┬─► write_practice ─► verify_practice ─► END     (kind = "practice")
           └─► write_report ─► END                         (kind = "report")

- write_practice:  text model writes a short practice sheet aimed at this student's mistakes
- verify_practice: plain code recomputes every arithmetic answer
- write_report:    text model writes a short progress note for the family, in their language

Teacher approval happens afterwards through the API (status 'ready' -> 'approved').
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.grading import QUESTION_TYPES, evaluate_expression, format_number, parse_number
from app.llm import ask_json, ask_text


class FollowupState(TypedDict, total=False):
    kind: str                     # "practice" or "report"
    student_name: str
    grade: int
    subject: str
    topic: str
    language: str
    teacher: str
    mistakes: list[dict]          # practice: [{question, student_answer, expected, mistake}]
    profile: dict                 # report: summary from analysis.student_profile
    num_questions: int
    # Outputs
    practice: dict                # {"intro": str, "questions": [...]}
    report: str


def _route(state: FollowupState) -> str:
    return "write_report" if state.get("kind") == "report" else "write_practice"


def write_practice(state: FollowupState) -> dict:
    mistakes = state.get("mistakes") or []
    count = int(state.get("num_questions", 4))
    if mistakes:
        focus = "This student made these mistakes:\n" + "\n".join(
            f"- '{m['question']}': wrote '{m['student_answer']}', expected '{m['expected']}' "
            f"({m.get('mistake') or 'mistake'})"
            for m in mistakes
        ) + "\nEvery question must practise fixing exactly these mistakes."
    else:
        focus = "This student got everything right. Write slightly harder challenge questions."

    reply = ask_json(
        "You write short, encouraging practice sheets for primary school students.",
        f"Student: {state['student_name']}, Grade {state['grade']} {state['subject']}, topic "
        f"'{state['topic']}'.\n{focus}\n\nWrite {count} new questions (not copies). Prefer type "
        "'number' for arithmetic (written like '2/7 + 3/7 =').\n"
        'Return JSON: {"intro": "<one friendly sentence to the student>", "questions": '
        '[{"text": "...", "type": "number|choice|text|short_answer", "answer": "...", '
        '"options": [...], "rubric": "..."}]}',
        temperature=0.4,
    )
    return {"practice": reply if isinstance(reply, dict) else {}}


def verify_practice(state: FollowupState) -> dict:
    practice = dict(state.get("practice") or {})
    questions = []
    for raw in practice.get("questions") or []:
        if not isinstance(raw, dict) or not str(raw.get("text") or "").strip():
            continue
        question = {
            "text": str(raw["text"]).strip(),
            "type": raw.get("type") if raw.get("type") in QUESTION_TYPES else "short_answer",
        }
        if question["type"] == "number":
            computed = evaluate_expression(question["text"])
            given = parse_number(str(raw.get("answer") or ""))
            if computed is None and given is None:
                continue
            question["answer"] = format_number(computed if computed is not None else given)
            question["verified"] = computed is not None
        else:
            for field in ("answer", "options", "rubric"):
                if raw.get(field):
                    question[field] = raw[field]
        questions.append(question)

    for index, question in enumerate(questions, start=1):
        question["number"] = str(index)
    practice["questions"] = questions
    practice["intro"] = str(practice.get("intro") or "Let's practise!").strip()
    return {"practice": practice}


def write_report(state: FollowupState) -> dict:
    profile = state.get("profile") or {}
    note = ask_text(
        "You write short, warm progress notes from a teacher to a student's family. Use simple "
        "words. Never shame the child. Write only the note.",
        f"Write the note in {state.get('language', 'English')}.\n"
        f"Student: {state['student_name']}. Teacher: {state.get('teacher') or 'the class teacher'}.\n"
        f"Scores on recent worksheets: {profile.get('history') or 'not enough data yet'}\n"
        f"Mistakes seen most often: {profile.get('top_mistakes') or 'none'}\n"
        f"Trend: {profile.get('trend') or 'unknown'}\n\n"
        "In 3-5 sentences: one thing the child is doing well, one thing to work on, and one "
        "simple way the family can help at home without any devices.",
        temperature=0.5,
    )
    return {"report": note.strip()}


def build_followup_graph():
    graph = StateGraph(FollowupState)
    graph.add_node("write_practice", write_practice)
    graph.add_node("verify_practice", verify_practice)
    graph.add_node("write_report", write_report)

    graph.add_conditional_edges(START, _route, {"write_practice": "write_practice",
                                                "write_report": "write_report"})
    graph.add_edge("write_practice", "verify_practice")
    graph.add_edge("verify_practice", END)
    graph.add_edge("write_report", END)
    return graph.compile()
