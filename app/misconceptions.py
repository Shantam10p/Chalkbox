"""The fixed list of fraction mistakes the diagnose step chooses from.

A fixed list keeps small models consistent and lets the class view count mistakes.
"""

MISCONCEPTIONS: dict[str, str] = {
    "added_denominators": "Added the bottom numbers as well as the top numbers (1/4 + 1/4 = 2/8)",
    "not_simplified": "Correct value but not written in simplest form (2/4 instead of 1/2)",
    "wrong_common_denominator": "Did not find a correct common bottom number before adding or subtracting",
    "bigger_denominator_bigger": "Thinks a bigger bottom number means a bigger fraction (1/8 > 1/4)",
    "whole_number_thinking": "Treated the top and bottom numbers as separate whole numbers",
    "calculation_error": "Right method, but a small arithmetic slip",
    "other": "A different mistake that does not fit the list",
}


def describe_all() -> str:
    return "\n".join(f"- {key}: {text}" for key, text in MISCONCEPTIONS.items())


def normalize(tag: str | None) -> str:
    tag = (tag or "").strip().lower()
    return tag if tag in MISCONCEPTIONS else "other"
