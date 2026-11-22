"""LLM wrapper returning validated Pydantic objects.

Uses Google Gemini (free tier) if GEMINI_API_KEY is set, otherwise Anthropic Claude
if ANTHROPIC_API_KEY is set. All four roles share the same model.
"""
import json
import os
import re
import time
from typing import Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv(override=True)  # .env wins over system-wide variables
T = TypeVar("T", bound=BaseModel)

# Comma-separated list. The free tier has a small DAILY quota per model, so if one model is used
# up (or unavailable) the app automatically tries the next one.
GEMINI_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_MODEL", "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",")
    if m.strip()
]
_DEAD_MODELS: set[str] = set()  # models whose daily quota is used up / not found this session
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def _clean(value: str | None) -> str:
    return (value or "").strip().strip('"').strip("'")


def _is_daily_quota(e: Exception) -> bool:
    t = str(e)
    return "429" in t and ("PerDay" in t or "per day" in t.lower())


def _is_missing(e: Exception) -> bool:
    return "404" in str(e) and "NOT_FOUND" in str(e)


def _is_transient(e: Exception) -> bool:
    return any(c in str(e) for c in ("429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))


def _call_gemini(system: str, user: str, key: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    for model in GEMINI_MODELS:
        if model in _DEAD_MODELS:
            continue
        for attempt in range(4):  # short outages / per-minute limits: wait and retry
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system, response_mime_type="application/json"
                    ),
                )
                return resp.text or ""
            except Exception as e:  # noqa: BLE001
                if _is_daily_quota(e) or _is_missing(e):
                    _DEAD_MODELS.add(model)  # do not waste time on it again; try the next model
                    break
                if _is_transient(e):
                    if attempt < 3:
                        time.sleep(10 * (attempt + 1))
                        continue
                    break  # still busy after retries: try the next model
                raise
    raise RuntimeError(
        "The free Gemini quota is used up (or the models are unavailable) for: "
        + ", ".join(GEMINI_MODELS)
        + ". Free-tier quotas reset daily (around 1:45 PM Nepal time). Wait and try again, "
        "or put another API key in .env."
    )


def _call_anthropic(system: str, user: str, key: str) -> str:
    from anthropic import Anthropic

    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    msg = Anthropic(api_key=key).messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _generate(system: str, user: str) -> str:
    gemini_key = _clean(os.getenv("GEMINI_API_KEY"))
    anthropic_key = _clean(os.getenv("ANTHROPIC_API_KEY"))
    if gemini_key and not gemini_key.startswith("your-"):
        return _call_gemini(system, user, gemini_key)
    if anthropic_key and not anthropic_key.startswith("your-"):
        return _call_anthropic(system, user, anthropic_key)
    raise RuntimeError(
        "No API key found. Copy .env.example to .env and set GEMINI_API_KEY (free) "
        "or ANTHROPIC_API_KEY."
    )


def ask_json(system: str, user: str, model_cls: Type[T], retries: int = 1) -> T:
    schema = json.dumps(model_cls.model_json_schema())
    system_full = (
        f"{system}\n\nReply with ONLY one JSON object matching this JSON schema, "
        f"no prose and no markdown fences:\n{schema}"
    )
    last_err = None
    for _ in range(retries + 1):
        text = _generate(system_full, user)
        match = re.search(r"\{.*\}", text, re.S)
        try:
            return model_cls.model_validate_json(match.group(0) if match else text)
        except (ValidationError, ValueError) as e:
            last_err = e
            user += "\n\nYour previous reply was not valid JSON for the schema. Try again."
    raise RuntimeError(f"Model returned invalid structured output: {last_err}")