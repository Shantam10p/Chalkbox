"""One small client for every model ChalkBox uses.

All agents call `ask_text`, `ask_json`, or `ask_vision_json`. Which server answers
(Ollama, NVIDIA API catalog, or a DGX Spark) is decided only by `.env`.
"""

import base64
import json
import mimetypes
import re
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from app.config import ModelEndpoint, settings

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class ModelOutputError(RuntimeError):
    """The model answered, but not with usable text."""


@lru_cache(maxsize=4)
def _client(base_url: str, api_key: str) -> OpenAI:
    # One retry only: a timed-out call on a slow machine would just time out again.
    return OpenAI(base_url=base_url, api_key=api_key, timeout=settings.request_timeout, max_retries=1)


def _clean(text: str) -> str:
    """Remove hidden reasoning blocks that some Qwen models emit."""
    return _THINK_BLOCK.sub("", text or "").strip()


def _no_think(model: str, prompt: str) -> str:
    # Hybrid Qwen3 models honour "/no_think"; instruct models never think, so skip it there.
    name = model.lower()
    if settings.disable_thinking and "qwen3" in name and "instruct" not in name:
        return f"{prompt}\n/no_think"
    return prompt


def _chat(endpoint: ModelEndpoint, messages: list[dict], temperature: float,
          max_tokens: int | None = None) -> str:
    response = _client(endpoint.base_url, endpoint.api_key).chat.completions.create(
        model=endpoint.model,
        messages=messages,
        temperature=temperature,
        # A cap stops a model from rambling (or "thinking") until the request times out.
        max_tokens=max_tokens or settings.max_tokens,
    )
    choice = response.choices[0]
    text = _clean(choice.message.content)
    if not text:
        hint = (
            " It used every token on hidden reasoning: use a non-thinking (instruct) model "
            "such as qwen3:4b-instruct." if choice.finish_reason == "length" else ""
        )
        raise ModelOutputError(f"{endpoint.model} returned an empty answer.{hint}")
    return text


def parse_json(text: str):
    """Parse JSON from a model reply, tolerating code fences and surrounding prose."""
    cleaned = _CODE_FENCE.sub("", _clean(text)).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost {...} or [...] in the reply.
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Model did not return valid JSON:\n{text[:500]}")


def ask_text(system: str, user: str, temperature: float = 0.4, max_tokens: int | None = None) -> str:
    endpoint = settings.text
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": _no_think(endpoint.model, user)},
    ]
    return _chat(endpoint, messages, temperature, max_tokens)


def ask_json(system: str, user: str, temperature: float = 0.2, retries: int = 1,
             max_tokens: int | None = None):
    """Asks for JSON and retries when a small model returns something unparseable."""
    for attempt in range(retries + 1):
        reply = ask_text(system + "\nRespond with JSON only.", user, temperature, max_tokens)
        try:
            return parse_json(reply)
        except ValueError:
            if attempt == retries:
                raise


def _image_data_uri(image_path: Path) -> str:
    mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def ask_vision_json(system: str, user: str, image_path: Path, temperature: float = 0.1, retries: int = 1):
    endpoint = settings.vision
    messages = [
        {"role": "system", "content": system + "\nRespond with JSON only."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {"url": _image_data_uri(Path(image_path))}},
            ],
        },
    ]
    for attempt in range(retries + 1):
        try:
            return parse_json(_chat(endpoint, messages, temperature))
        except ValueError:
            if attempt == retries:
                raise
