"""Exact grading in plain code. The AI only reads answers; this decides right or wrong."""

import re
from fractions import Fraction

_MIXED = re.compile(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$")  # e.g. "1 1/2"
_SIMPLE = re.compile(r"^(-?\d+)\s*/\s*(\d+)$")          # e.g. "3/4"


def parse_number(text: str) -> Fraction | None:
    """Turns a written answer into an exact number. Returns None if it can't be understood."""
    if text is None:
        return None
    cleaned = text.strip().replace("⁄", "/").replace("÷", "/").replace(" ", " ")
    if not cleaned:
        return None
    try:
        if match := _MIXED.match(cleaned):
            whole, num, den = (int(g) for g in match.groups())
            if den == 0:
                return None
            sign = -1 if whole < 0 else 1
            return Fraction(whole) + sign * Fraction(num, den)
        if match := _SIMPLE.match(cleaned):
            num, den = (int(g) for g in match.groups())
            return None if den == 0 else Fraction(num, den)
        return Fraction(cleaned)  # whole numbers and decimals
    except (ValueError, ZeroDivisionError):
        return None


def is_simplified(text: str) -> bool:
    """True if a fraction is written in lowest terms (3/4 yes, 6/8 no)."""
    cleaned = text.strip()
    match = _MIXED.match(cleaned) or _SIMPLE.match(cleaned)
    if not match:
        return True  # whole numbers and decimals count as simplified
    num, den = int(match.groups()[-2]), int(match.groups()[-1])
    return Fraction(num, den).denominator == den


def grade_answer(student: str, key: str, require_simplified: bool = False) -> tuple[bool | None, str | None]:
    """Returns (correct, misconception_found_by_code).

    correct is None when the student's answer can't be parsed (the teacher should check it).
    """
    if not (student or "").strip():
        return False, None  # blank answer
    student_value, key_value = parse_number(student), parse_number(key)
    if student_value is None or key_value is None:
        return None, None
    if student_value != key_value:
        return False, None
    if require_simplified and not is_simplified(student):
        return False, "not_simplified"
    return True, None
