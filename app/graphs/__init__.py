"""ChalkBox workflows, built as LangGraph graphs.

Each former "agent" is a node (one step) inside a graph.

    check.py     Graph 1 - read a worksheet photo, mark it, teacher review (interrupt),
                           AI-grade open questions, diagnose mistakes + feedback
    plan.py      Graph 2 - 6-part lesson + typed worksheet + answer key, verified by code
    followup.py  Graph 3 - personalized practice sheet or parent note for one student

The Check graph pauses mid-run for the teacher, so it uses the SQLite checkpoint store.
Plan and Follow-up finish in one go; the teacher approves their output through the API.
"""

from functools import lru_cache

from app.graphs.check import build_check_graph
from app.graphs.checkpoints import get_checkpointer
from app.graphs.followup import build_followup_graph
from app.graphs.plan import build_plan_graph


@lru_cache(maxsize=1)
def check_graph():
    return build_check_graph(get_checkpointer())


@lru_cache(maxsize=1)
def plan_graph():
    return build_plan_graph()


@lru_cache(maxsize=1)
def followup_graph():
    return build_followup_graph()
