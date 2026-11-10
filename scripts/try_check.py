"""Runs the Check graph end to end on a generated sample worksheet.

Run from the project root:  python -m scripts.try_check [path/to/photo.jpg]
Without a path it draws a typed sample sheet where Q2 is wrong (2/8 instead of 1/2).
"""

import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

from langgraph.types import Command
from PIL import Image, ImageDraw, ImageFont

from app.graphs.check import build_check_graph
from app.graphs.checkpoints import get_checkpointer

QUESTIONS = {"1": "1/5 + 2/5", "2": "1/4 + 1/4", "3": "3/8 + 1/8", "4": "2/6 + 1/6"}
ANSWER_KEY = {"1": "3/5", "2": "1/2", "3": "1/2", "4": "1/2"}
STUDENT_ANSWERS = {"1": "3/5", "2": "2/8", "3": "4/8", "4": "1/2"}


def draw_sample(path: Path) -> None:
    image = Image.new("RGB", (900, 620), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 30), "Grade 4 - Adding Fractions", fill="black", font=font)
    draw.text((40, 100), "Name: Ravi", fill="black", font=font)
    for i, (number, question) in enumerate(QUESTIONS.items()):
        y = 200 + i * 100
        draw.text((40, y), f"{number}.  {question} =", fill="black", font=font)
        draw.rectangle((520, y - 10, 760, y + 55), outline="black", width=3)
        draw.text((545, y), STUDENT_ANSWERS[number], fill="blue", font=font)
    image.save(path)


def main() -> None:
    graph = build_check_graph(get_checkpointer())
    config = {"configurable": {"thread_id": f"check-{uuid.uuid4()}"}}

    with tempfile.TemporaryDirectory() as tmp:
        image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tmp) / "sample.png"
        if len(sys.argv) <= 1:
            draw_sample(image_path)

        start = time.perf_counter()
        state = graph.invoke(
            {"image_path": str(image_path), "questions": QUESTIONS, "answer_key": ANSWER_KEY},
            config,
        )
        while "__interrupt__" in state:
            pause = state["__interrupt__"][0].value
            print("Teacher review needed:", json.dumps(pause["flagged"], indent=2))
            print("(auto-accepting the readings for this test)")
            state = graph.invoke(Command(resume={}), config)

    print(f"\nStudent: {state.get('student_name')}   Score: {state.get('score')}")
    for number, result in state["results"].items():
        mark = {True: "OK ", False: "X  ", None: "?  "}[result.get("correct")]
        line = f"  Q{number} {mark} wrote {result['answer']!r:8}"
        if result.get("misconception"):
            line += f"  [{result['misconception']}] {result.get('explanation', '')}"
        print(line)
    print(f"\nFeedback: {state.get('feedback')}")
    print(f"Took {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
