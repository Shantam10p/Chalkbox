"""The student AI helper: course-related questions only, hints instead of answers.

Guardrails:
- The model is told the class's actual topics and must decline anything else. When it marks
  a question off-topic, code replaces its reply with a fixed, friendly redirect.
- It never solves worksheet or practice questions; it gives one hint or a similar example.
- Signs that a student is upset or unsafe are flagged for the teacher.
- Every conversation is stored, and the teacher can read it.
"""

from app import analysis, repo
from app.llm import ask_json

MAX_MESSAGE_CHARS = 500
HISTORY_TURNS = 8          # earlier messages the helper sees for context
MESSAGES_PER_HOUR = 30


def _off_topic_reply(topics: list[str]) -> str:
    names = [t.split(": ", 1)[-1] for t in topics[:2]]
    examples = ", ".join(n[:1].lower() + n[1:] for n in names) or "your class work"
    return (f"I can only help with your schoolwork, like {examples}. "
            "What would you like to practise?")


def _practice_questions(student_id: int) -> list[str]:
    texts = []
    for sheet in repo.student_practice(student_id)[:3]:
        texts += [q.get("text", "") for q in (sheet.get("content") or {}).get("questions", [])]
    return [t for t in texts if t][:12]


def reply(student_id: int, message: str) -> dict:
    """Answers one student message. Returns {"reply", "on_topic", "flagged"}."""
    student = repo.get_student(student_id)
    class_ = repo.get_class(student["class_id"])
    topics = repo.class_topics(class_["id"])[:12]
    profile = analysis.student_profile(student_id, approved_only=True) or {}
    mistakes = [m["description"] for m in profile.get("top_mistakes", [])[:3]]
    practice = _practice_questions(student_id)
    history = repo.helper_messages(student_id, limit=HISTORY_TURNS)

    conversation = "\n".join(
        f"{'Student' if m['role'] == 'student' else 'Helper'}: {m['content']}" for m in history
    )
    first_name = student["name"].split()[0]
    system = (
        f"You are ChalkBox Helper, a kind study buddy for {first_name}, a Grade {class_['grade']} "
        f"student in {class_['name']} (teacher: {class_.get('teacher') or 'their teacher'}).\n"
        "Rules you must always follow:\n"
        "1. Only help with these school topics from the student's class: "
        f"{'; '.join(topics) or 'their Grade ' + str(class_['grade']) + ' school subjects'}. "
        "Questions about how to study these topics are fine. Anything else (games, shows, "
        "celebrities, other people, chatting, jokes, personal advice, other subjects) is off-topic.\n"
        "2. Never give the final answer to a worksheet or practice question. Give ONE hint, or "
        "show a similar example with different numbers, then let the student try.\n"
        f"3. Use simple words for a Grade {class_['grade']} student. Reply in 1 to 4 short "
        "sentences, in the same language the student writes in.\n"
        "4. Never ask for or repeat personal information (address, phone, passwords).\n"
        "5. If the student seems upset, scared, unsafe, or mentions being hurt, kindly tell them "
        "to talk to their teacher or a trusted adult right away, and set needs_teacher to true.\n"
        + (f"This student often makes these mistakes: {'; '.join(mistakes)}. Aim hints at them.\n"
           if mistakes else "")
        + (f"The student's practice questions (never solve these for them): {'; '.join(practice)}\n"
           if practice else "")
    )
    user = (
        (f"Conversation so far:\n{conversation}\n\n" if conversation else "")
        + f"Student's new message: {message}\n\n"
        'Return JSON: {"on_topic": true or false, "needs_teacher": true or false, '
        '"reply": "<your reply to the student>"}'
    )

    result = ask_json(system, user, temperature=0.3, max_tokens=400)
    if not isinstance(result, dict):
        result = {}
    on_topic = result.get("on_topic") is not False
    flagged = result.get("needs_teacher") is True
    text = str(result.get("reply") or "").strip()

    if flagged:
        text = text or ("That sounds hard. Please talk to your teacher or a trusted adult "
                        "right away. They want to help you.")
    elif not on_topic or not text:
        text = _off_topic_reply(topics)
    return {"reply": text[:1200], "on_topic": on_topic or flagged, "flagged": flagged}
