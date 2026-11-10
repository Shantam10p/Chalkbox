"""Smoke test: confirms the configured text and vision models answer.

Run from the project root:  python -m scripts.check_models
"""

import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.llm import ask_json, ask_vision_json


def _test_image(path: Path) -> None:
    """Draws a tiny fake worksheet answer so the vision model has something to read."""
    image = Image.new("RGB", (480, 200), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    draw.text((30, 30), "Name: Ravi", fill="black", font=font)
    draw.text((30, 110), "Q1: 3/4", fill="black", font=font)
    image.save(path)


def check_text() -> None:
    print(f"Text model:   {settings.text.model} @ {settings.text.base_url}")
    start = time.perf_counter()
    result = ask_json(
        "You are a grading assistant.",
        'Return {"sum": "<the answer to 1/4 + 1/4 as a simplified fraction>"}',
    )
    print(f"  reply: {result}  ({time.perf_counter() - start:.1f}s)")


def check_vision() -> None:
    print(f"Vision model: {settings.vision.model} @ {settings.vision.base_url}")
    with tempfile.TemporaryDirectory() as tmp:
        image_path = Path(tmp) / "test.png"
        _test_image(image_path)
        start = time.perf_counter()
        result = ask_vision_json(
            "You read student worksheets.",
            'Read the image and return {"name": "...", "q1": "..."}',
            image_path,
        )
        print(f"  reply: {result}  ({time.perf_counter() - start:.1f}s)")


if __name__ == "__main__":
    for check in (check_text, check_vision):
        try:
            check()
        except Exception as error:  # report every failure, keep going
            print(f"  FAILED: {error}")
