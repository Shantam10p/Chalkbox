"""Runs the Check graph directly (no server, no database) on one worksheet photo.

Run from the project root:  python -m scripts.try_check [path/to/photo.jpg]
Without a path it draws the sample fractions worksheet filled in by "Ravi".
"""

import json
import sys
import tempfile
import time
import uuid
from pathlib import Path

from langgraph.types import Command

from app.graphs import check_graph
from scripts.samples import FRACTIONS_WORKSHEET, SAMPLE_ANSWERS, draw_worksheet


def main() -> None:
    config = {"configurable": {"thread_id": f"try-{uuid.uuid4()}"}}
    with tempfile.TemporaryDirectory() as tmp:
        if len(sys.argv) > 1:
            image_path = Path(sys.argv[1])
        else:
            image_path = Path(tmp) / "sample.png"
            draw_worksheet(image_path, FRACTIONS_WORKSHEET, SAMPLE_ANSWERS, "Ravi")

        start = time.perf_counter()
        state = check_graph().invoke(
            {"image_path": str(image_path), "questions": FRACTIONS_WORKSHEET["questions"],
             "misconceptions": FRACTIONS_WORKSHEET["misconceptions"]},
            config,
        )
        while "__interrupt__" in state:
            pause = state["__interrupt__"][0].value
            print("Teacher review needed:", json.dumps(pause["flagged"], indent=2))
            print("(auto-accepting the readings for this test)")
            state = check_graph().invoke(Command(resume={}), config)

    print(f"\nStudent: {state.get('student_name')}   "
          f"Score: {state.get('score_correct')}/{state.get('score_total')}")
    for number, result in state["results"].items():
        mark = {True: "OK", False: "X ", None: "? "}[result.get("correct")]
        line = f"  Q{number} {mark} [{result.get('graded_by')}] wrote {result['answer']!r}"
        if result.get("misconception"):
            line += f"  <{result['misconception']}>"
        if result.get("explanation"):
            line += f"  {result['explanation']}"
        print(line)
    print(f"\nFeedback: {state.get('feedback')}")
    print(f"Took {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
