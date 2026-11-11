"""Sample data shared by the seed and test scripts."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.misconceptions import FRACTIONS

FRACTIONS_WORKSHEET = {
    "title": "Adding Fractions",
    "subject": "Math",
    "topic": "Adding fractions with the same denominator",
    "misconceptions": FRACTIONS,
    "questions": [
        {"number": "1", "text": "1/5 + 2/5 =", "type": "number", "answer": "3/5"},
        {"number": "2", "text": "1/4 + 1/4 =", "type": "number", "answer": "1/2", "simplify": True},
        {"number": "3", "text": "3/8 + 1/8 =", "type": "number", "answer": "1/2"},
        {"number": "4", "text": "2/6 + 3/6 =", "type": "number", "answer": "5/6"},
        {"number": "5", "text": "1/3 + 1/3 =", "type": "number", "answer": "2/3"},
        {"number": "6", "text": "3/10 + 4/10 =", "type": "number", "answer": "7/10"},
        {"number": "7", "text": "Which is bigger?", "type": "choice",
         "options": ["A. 1/4", "B. 1/8"], "answer": "A"},
        {"number": "8", "text": "Explain why 1/4 + 1/4 is not 2/8.", "type": "short_answer",
         "rubric": "Says the bottom number (denominator) stays the same and only the top "
                   "numbers are added, or that 2/8 is the same as 1/4 so it is too small."},
    ],
}

# A student who makes the classic mistakes: Q2, Q5 (added denominators), Q7, Q8 wrong.
SAMPLE_ANSWERS = {
    "1": "3/5", "2": "2/8", "3": "4/8", "4": "5/6", "5": "2/6", "6": "7/10",
    "7": "B", "8": "Because you add the bottom numbers too",
}

CLASS = {"name": "Grade 4A", "grade": 4, "teacher": "Dave"}

# Family languages used in the demo: English, Spanish, Hindi, Nepali, Tagalog.
LANGUAGES = ["English", "Spanish", "Hindi", "Nepali", "Tagalog"]

STUDENTS = [
    ("Maya Johnson", "English"), ("Lucas Garcia", "Spanish"), ("Ava Thompson", "English"),
    ("Noah Williams", "English"), ("Sofia Hernandez", "Spanish"), ("Ethan Brown", "English"),
    ("Priya Patel", "Hindi"), ("Liam Carter", "English"), ("Isabella Martinez", "Spanish"),
    ("Mateo Lopez", "Spanish"), ("Chloe Kim", "English"), ("Aarav Sharma", "Hindi"),
    ("Olivia Davis", "English"), ("Daniel Nguyen", "English"), ("Grace Wilson", "English"),
    ("Sanjay Thapa", "Nepali"), ("Emma Rodriguez", "Spanish"), ("Jacob Anderson", "English"),
    ("Angel Reyes", "Tagalog"), ("Mia Santos", "Tagalog"), ("James Taylor", "English"),
    ("Anjali Gurung", "Nepali"), ("Benjamin Lee", "English"), ("Camila Torres", "Spanish"),
    ("Elijah Jackson", "English"), ("Nikhil Mehta", "Hindi"), ("Hannah White", "English"),
    ("Jasmine Cruz", "Tagalog"), ("Samuel Moore", "English"), ("Pooja Rai", "Nepali"),
]


def _font(size: int):
    # Segoe Print looks hand-written on Windows; fall back to Arial or the default font.
    for name in ("segoepr.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_worksheet(path: Path, worksheet: dict, answers: dict[str, str], name: str) -> None:
    """Draws a filled-in worksheet in the ChalkBox layout (for testing without paper)."""
    questions = worksheet["questions"]
    height = 230 + 110 * len(questions)
    image = Image.new("RGB", (1100, height), "white")
    draw = ImageDraw.Draw(image)
    printed, written = _font(34), _font(36)

    draw.text((40, 30), f"ChalkBox - {worksheet['title']}", fill="black", font=printed)
    draw.text((40, 100), "Name:", fill="black", font=printed)
    draw.rectangle((160, 90, 600, 150), outline="black", width=3)
    draw.text((180, 95), name, fill=(20, 40, 160), font=written)

    for i, question in enumerate(questions):
        y = 200 + i * 110
        text = f"{question['number']}. {question['text']}"
        if question["type"] == "choice":
            text += "   " + "   ".join(question["options"])
        draw.text((40, y), text, fill="black", font=printed)
        box_x = 40 if question["type"] == "short_answer" else 700
        box_y = y + 45 if question["type"] == "short_answer" else y - 10
        draw.rectangle((box_x, box_y, 1060, box_y + 60), outline="black", width=3)
        draw.text((box_x + 15, box_y + 5), answers.get(question["number"], ""),
                  fill=(20, 40, 160), font=written)
    image.save(path)
