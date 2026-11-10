"""ChalkBox workflows, built as LangGraph graphs.

Each former "agent" is now a node (one step) inside a graph. Teacher checkpoints use
LangGraph's `interrupt`, and progress is saved to SQLite so a review can be finished later.

    check.py     Graph 1 - read a worksheet photo, mark it, teacher review, diagnose + feedback
    plan.py      Graph 2 - 6-part lesson + worksheet + answer key, teacher approval   (to build)
    followup.py  Graph 3 - practice sheets + parent notes per student, teacher approval (to build)
"""
