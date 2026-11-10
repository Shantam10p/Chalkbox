"""Exact grading in plain code. The AI only reads answers; code decides right or wrong
for every question that has one exact answer. Open questions are left for the AI."""

import ast
import operator
import re
import string
from fractions import Fraction

QUESTION_TYPES = ("number", "choice", "text", "short_answer")

_MIXED = re.compile(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$")  # e.g. "1 1/2"
_SIMPLE = re.compile(r"^(-?\d+)\s*/\s*(\d+)$")          # e.g. "3/4"


# ---------------------------------------------------------------- numbers

def parse_number(text: str | None) -> Fraction | None:
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


def format_number(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_MATH_RUN = re.compile(r"[\d\s+\-*/().]+")


def _eval_node(node) -> Fraction:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError
        return _OPS[type(node.op)](left, right)
    raise ValueError("unsupported expression")


def evaluate_expression(question_text: str) -> Fraction | None:
    """Works out the exact answer to an arithmetic question such as '3/8 + 1/8 =' or
    'What is 12 x 4?'. Returns None if the question isn't plain arithmetic."""
    # Bracket each written fraction first, so "1/4 ÷ 1/2" means (1/4) / (1/2), not 1/4/1/2.
    text = re.sub(r"(\d+)\s*/\s*(\d+)", r"(\1/\2)", question_text)
    text = text.replace("×", "*").replace("÷", "/").replace("−", "-")
    text = re.sub(r"(?<=[\d)])\s*[xX]\s*(?=[\d(])", "*", text)
    def has_operation(run: str) -> bool:
        # A lone fraction like "(1/4)" is a number, not a sum to work out.
        outside_brackets = re.sub(r"\([^()]*\)", "", run)
        return any(op in outside_brackets for op in "+-*/") and any(ch.isdigit() for ch in run)

    runs = _MATH_RUN.findall(text)
    candidates = [run.strip() for run in runs if has_operation(run)]
    if not candidates and question_text.strip().endswith("="):
        # "10 / 4 =" or "6/8 =": a trailing equals sign means "work this out".
        candidates = [run.strip() for run in runs if any(ch.isdigit() for ch in run)]
    if not candidates:
        return None
    expression = max(candidates, key=len).strip(" =")
    try:
        return _eval_node(ast.parse(expression, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError):
        return None


def grade_number(student: str, key: str, require_simplified: bool = False) -> tuple[bool | None, str | None]:
    """Returns (correct, misconception_found_by_code). correct is None if unreadable."""
    if not (student or "").strip():
        return False, None
    student_value, key_value = parse_number(student), parse_number(key)
    if student_value is None or key_value is None:
        return None, None
    if student_value != key_value:
        return False, None
    if require_simplified and not is_simplified(student):
        return False, "not_simplified"
    return True, None


# Kept for backwards compatibility with earlier scripts.
grade_answer = grade_number


# ---------------------------------------------------------------- choice and text

def _normalize_text(text: str) -> str:
    text = (text or "").casefold().strip()
    text = text.strip(string.punctuation + " ")
    return re.sub(r"\s+", " ", text)


def choice_letter(student: str, options: list[str] | None) -> str | None:
    """Turns 'b', 'B.', '(B)', or the option's text into a letter like 'B'."""
    cleaned = (student or "").strip().strip("()[] ")
    if not cleaned:
        return None
    if len(cleaned) == 1 and cleaned.isalpha():
        return cleaned.upper()
    if len(cleaned) >= 2 and cleaned[0].isalpha() and cleaned[1] in ".):":
        return cleaned[0].upper()
    for index, option in enumerate(options or []):
        option_text = re.sub(r"^[A-Za-z][.):]\s*", "", option)
        if _normalize_text(option_text) == _normalize_text(cleaned):
            return string.ascii_uppercase[index]
    return None


def grade_choice(student: str, key: str, options: list[str] | None) -> bool | None:
    if not (student or "").strip():
        return False
    letter = choice_letter(student, options)
    return None if letter is None else letter == key.strip().upper()[:1]


def grade_text(student: str, key: str, accept: list[str] | None = None) -> bool:
    if not (student or "").strip():
        return False
    allowed = {_normalize_text(key), *(_normalize_text(a) for a in accept or [])}
    return _normalize_text(student) in allowed


# ---------------------------------------------------------------- dispatcher

def grade_question(question: dict, student: str) -> dict:
    """Grades one answer. Returns {correct, misconception, graded_by}.

    graded_by is 'code' when code decided, or 'ai_pending' when the AI must judge.
    """
    kind = question.get("type", "short_answer")
    answer = str(question.get("answer") or "")

    if kind == "number":
        correct, misconception = grade_number(student, answer, bool(question.get("simplify")))
        return {"correct": correct, "misconception": misconception, "graded_by": "code"}
    if kind == "choice":
        return {"correct": grade_choice(student, answer, question.get("options")),
                "misconception": None, "graded_by": "code"}
    if kind == "text":
        return {"correct": grade_text(student, answer, question.get("accept")),
                "misconception": None, "graded_by": "code"}
    # short_answer (and anything unknown): the AI judges it against the rubric.
    if not (student or "").strip():
        return {"correct": False, "misconception": None, "graded_by": "code"}
    return {"correct": None, "misconception": None, "graded_by": "ai_pending"}
