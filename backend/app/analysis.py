"""Class and student insights, computed in plain code from stored answers."""

from collections import Counter, defaultdict

from app import misconceptions as mc
from app import repo

# Score ratio boundaries for grouping students.
RETEACH_BELOW = 0.5
READY_FROM = 0.8


def worksheet_summary(worksheet_id: int) -> dict | None:
    worksheet = repo.get_worksheet(worksheet_id)
    if worksheet is None:
        return None
    descriptions = mc.with_defaults(worksheet["misconceptions"])
    subs = [s for s in repo.list_submissions(worksheet_id, with_answers=True)
            if s["status"] in ("graded", "approved")]

    per_question: dict[str, dict] = {
        str(q["number"]): {"number": str(q["number"]), "text": q["text"], "type": q["type"],
                           "attempts": 0, "correct": 0}
        for q in worksheet["questions"]
    }
    mistakes: dict[str, list[str]] = defaultdict(list)
    groups = {"reteach": [], "practice": [], "ready": []}
    ratios = []

    for sub in subs:
        who = sub.get("student_name") or sub.get("student_name_read") or f"Sheet {sub['id']}"
        for answer in sub["answers"]:
            stats = per_question.get(answer["question_no"])
            if stats is not None:
                stats["attempts"] += 1
                stats["correct"] += answer["correct"] is True
            if answer["correct"] is False and answer["misconception"]:
                mistakes[answer["misconception"]].append(who)
        if sub["score_total"]:
            ratio = (sub["score_correct"] or 0) / sub["score_total"]
            ratios.append(ratio)
            group = "reteach" if ratio < RETEACH_BELOW else "ready" if ratio >= READY_FROM else "practice"
            groups[group].append({"submission_id": sub["id"], "student": who,
                                  "score": f"{sub['score_correct']}/{sub['score_total']}"})

    for stats in per_question.values():
        stats["accuracy"] = round(stats["correct"] / stats["attempts"], 2) if stats["attempts"] else None

    # count = how many students made the mistake (one student repeating it counts once);
    # times = how often it appeared in total.
    top_mistakes = sorted(
        (
            {"id": key, "description": descriptions.get(key, key), "count": len(set(names)),
             "times": len(names), "share": round(len(set(names)) / len(subs), 2) if subs else 0,
             "students": sorted(set(names))}
            for key, names in mistakes.items()
        ),
        key=lambda m: (m["count"], m["times"]),
        reverse=True,
    )

    return {
        "worksheet_id": worksheet_id,
        "title": worksheet["title"],
        "graded": len(subs),
        "approved": sum(1 for s in subs if s["status"] == "approved"),
        "average": round(sum(ratios) / len(ratios), 2) if ratios else None,
        "questions": list(per_question.values()),
        "top_mistakes": top_mistakes,
        "groups": groups,
    }


def recent_mistakes(class_id: int, limit: int = 2) -> list[str]:
    """The class's most common mistakes on its latest graded worksheet (for 'Fix yesterday')."""
    worksheet_id = repo.latest_graded_worksheet(class_id)
    if worksheet_id is None:
        return []
    summary = worksheet_summary(worksheet_id)
    return [
        f"{m['description']} ({m['count']} student{'s' if m['count'] != 1 else ''})"
        for m in summary["top_mistakes"][:limit]
        if m["id"] != "other"
    ]


def student_profile(student_id: int) -> dict | None:
    student = repo.get_student(student_id)
    if student is None:
        return None

    history: dict[int, dict] = {}
    mistake_counts: Counter = Counter()
    descriptions: dict[str, str] = {}
    for row in repo.student_answers(student_id):
        # Rows for the same submission share one history entry.
        history.setdefault(row["submission_id"], {
            "submission_id": row["submission_id"], "worksheet_id": row["worksheet_id"],
            "title": row["title"], "topic": row["topic"], "date": row["created_at"],
            "score": f"{row['score_correct']}/{row['score_total']}",
            "ratio": (row["score_correct"] or 0) / row["score_total"] if row["score_total"] else None,
        })
        if row["correct"] == 0 and row["misconception"]:
            mistake_counts[row["misconception"]] += 1
            if row["worksheet_id"] not in descriptions:
                worksheet = repo.get_worksheet(row["worksheet_id"])
                descriptions.update(mc.with_defaults(worksheet["misconceptions"]))

    items = list(history.values())
    ratios = [i["ratio"] for i in items if i["ratio"] is not None]
    if len(ratios) >= 2:
        change = ratios[-1] - ratios[0]
        trend = "improving" if change > 0.1 else "slipping" if change < -0.1 else "steady"
    else:
        trend = "not enough data yet"

    return {
        "student": student,
        "history": [{k: v for k, v in i.items() if k != "ratio"} for i in items],
        "average": round(sum(ratios) / len(ratios), 2) if ratios else None,
        "trend": trend,
        "top_mistakes": [
            {"id": key, "description": descriptions.get(key, key), "count": count}
            for key, count in mistake_counts.most_common(5)
        ],
    }


def student_mistakes_on(worksheet_id: int, student_id: int) -> list[dict]:
    """The student's wrong answers on one worksheet, for building a practice sheet."""
    worksheet = repo.get_worksheet(worksheet_id)
    questions = {str(q["number"]): q for q in worksheet["questions"]}
    descriptions = mc.with_defaults(worksheet["misconceptions"])
    subs = [s for s in repo.list_submissions(worksheet_id, with_answers=True)
            if s["student_id"] == student_id and s["status"] in ("graded", "approved")]
    if not subs:
        return []
    mistakes = []
    for answer in subs[-1]["answers"]:
        if answer["correct"] is False:
            question = questions.get(answer["question_no"], {})
            mistakes.append({
                "question": question.get("text", ""),
                "student_answer": answer["student_answer"] or "(blank)",
                "expected": question.get("answer") or question.get("rubric") or "",
                "mistake": descriptions.get(answer["misconception"] or "", ""),
            })
    return mistakes
