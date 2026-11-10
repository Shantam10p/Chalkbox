"""Lists of common mistakes the diagnose step chooses from.

Each worksheet carries its own list (the Plan graph writes one per topic). A fixed list
keeps small models consistent and lets the class view count mistakes.
"""

FRACTIONS: dict[str, str] = {
    "added_denominators": "Added the bottom numbers as well as the top numbers (1/4 + 1/4 = 2/8)",
    "not_simplified": "Correct value but not written in simplest form (2/4 instead of 1/2)",
    "wrong_common_denominator": "Did not find a correct common bottom number before adding or subtracting",
    "bigger_denominator_bigger": "Thinks a bigger bottom number means a bigger fraction (1/8 > 1/4)",
    "whole_number_thinking": "Treated the top and bottom numbers as separate whole numbers",
    "calculation_error": "Right method, but a small arithmetic slip",
    "other": "A different mistake that does not fit the list",
}

# Used when a worksheet has no topic-specific list.
GENERAL: dict[str, str] = {
    "concept_gap": "Does not yet understand the main idea being tested",
    "calculation_error": "Right method, but a small slip",
    "misread_question": "Answered a different question than the one asked",
    "incomplete_answer": "Started correctly but did not finish or explain fully",
    "other": "A different mistake that does not fit the list",
}

# Always available, even if a topic list forgets them (they are set by code).
_BUILT_IN = {
    "not_simplified": FRACTIONS["not_simplified"],
    "other": GENERAL["other"],
}


def with_defaults(misconceptions: dict[str, str] | None) -> dict[str, str]:
    base = dict(misconceptions or GENERAL)
    for key, text in _BUILT_IN.items():
        base.setdefault(key, text)
    return base


def describe(misconceptions: dict[str, str]) -> str:
    return "\n".join(f"- {key}: {text}" for key, text in misconceptions.items())


def normalize(tag: str | None, allowed: dict[str, str]) -> str:
    tag = (tag or "").strip().lower()
    return tag if tag in allowed else "other"
