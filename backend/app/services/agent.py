"""LLM agent classification via LiteLLM."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from email.utils import parseaddr

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.services.mail import ScrapedEmail

logger = logging.getLogger(__name__)

MAX_BODY_CHARS = 12_000

SYSTEM_PROMPT = """\
You are an office task extraction assistant. Given an email, extract structured task information.

Return a JSON object with exactly these keys:
- person_name: display name of the sender or person the task involves
- person_email: their email address if known, otherwise null
- task_title: a short actionable task title (imperative, under 100 chars), or null if not actionable
- summary: 1-3 sentence summary of what needs to be done (plain text, no line breaks)

If the email is clearly not actionable (newsletters, automated notifications, receipts), \
set task_title to null.

Do not analyze, explain, or use markdown. Output only the JSON object. Keep summary under 300 characters.

Example:
{"person_name": "Jane Doe", "person_email": "jane@example.com", "task_title": "Review Q3 budget", "summary": "Jane asked for feedback on the budget by Friday."}"""


class _ClassificationResponse(BaseModel):
    person_name: str
    person_email: str | None = None
    task_title: str | None = None
    summary: str


# Groq json_schema (strict) produces valid JSON with escaped strings — json_object
# alone can still emit unescaped newlines inside summary and break json.loads.
_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "person_name": {"type": "string"},
        "person_email": {"type": ["string", "null"]},
        "task_title": {"type": ["string", "null"]},
        "summary": {"type": "string"},
    },
    "required": ["person_name", "person_email", "task_title", "summary"],
    "additionalProperties": False,
}


@dataclass
class Classification:
    """Structured output produced by the agent for a single email."""

    person_name: str
    person_email: str | None
    task_title: str
    summary: str


def _build_user_message(email: ScrapedEmail) -> str:
    body = email.body
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "\n…[truncated]"

    return f"From: {email.sender}\nSubject: {email.subject}\n\n{body}"


def _strip_reasoning_blocks(text: str) -> str:
    # Reasoning models (e.g. groq/qwen/qwen3-6-27b) wrap the real answer in
    # thinking tags before the JSON. Tags are built via concatenation so they
    # are not accidentally stripped by tooling. Add new patterns here if a
    # model uses a different tag format.
    if "<think" not in text.lower():
        return text

    think = "think"  # noqa: used to build tag patterns safely
    patterns = (
        rf"<{think}>.*?</{think}>",
        r"<think>.*?</think>",
        r"<thinking>.*?</thinking>",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def _extract_json(raw: str) -> str:
    # Normalise model output before json.loads. Try a direct parse first so
    # valid JSON is never passed through the reasoning-block stripper.
    text = raw.strip().lstrip("\ufeff")
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    text = _strip_reasoning_blocks(text)

    # Unwrap ```json fences if the model wraps output despite instructions.
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    elif text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        # Last resort: grab the outermost { ... }. Can mis-parse if { appears
        # inside a string value before the real object.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return text[start : end + 1]
    return text


def _parse_classification(raw: str, email: ScrapedEmail) -> Classification | None:
    extracted = _extract_json(raw)
    try:
        data = json.loads(extracted)
        parsed = _ClassificationResponse.model_validate(data)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Invalid classification JSON (%s at pos %d, len=%d): %r",
            exc.msg,
            exc.pos,
            len(raw),
            raw[:500],
        )
        return None
    except ValidationError as exc:
        logger.warning("Classification validation failed: %s", exc)
        return None

    if not parsed.task_title or not parsed.task_title.strip():
        return None

    person_name = parsed.person_name.strip()
    summary = parsed.summary.strip()
    if not person_name or not summary:
        return None

    _, sender_addr = parseaddr(email.sender)
    person_email = parsed.person_email or sender_addr or None

    return Classification(
        person_name=person_name,
        person_email=person_email,
        task_title=parsed.task_title.strip(),
        summary=summary,
    )


def _groq_reasoning_kwargs(model: str) -> dict:
    # Qwen on Groq defaults to thinking mode and may return analysis instead of
    # JSON. Groq docs: use reasoning_effort="none" for non-thinking mode and
    # reasoning_format="hidden" (required alongside json_object mode).
    lowered = model.lower()
    if "qwen" in lowered:
        return {"reasoning_effort": "none", "reasoning_format": "hidden"}
    if "gpt-oss" in lowered:
        return {"reasoning_format": "hidden"}
    return {}


def _groq_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "email_classification",
            "schema": _CLASSIFICATION_SCHEMA,
            "strict": True,
        },
    }


def _completion_kwargs(settings) -> dict:
    """Build LiteLLM kwargs for the configured provider."""
    model = settings.litellm_model
    kwargs: dict = {"model": model, "temperature": 0, "max_tokens": 1024}

    if model.startswith("groq/"):
        # Pass key explicitly so LiteLLM routes to Groq, not OpenAI.
        kwargs["api_key"] = settings.groq_api_key
        kwargs["response_format"] = _groq_response_format()
        kwargs.update(_groq_reasoning_kwargs(model))
    elif model.startswith("openai/"):
        kwargs["api_key"] = settings.openai_api_key
        kwargs["response_format"] = {"type": "json_object"}
    elif model.startswith("anthropic/"):
        kwargs["api_key"] = settings.anthropic_api_key

    return kwargs


async def classify_email(email: ScrapedEmail) -> Classification | None:
    """Classify a scraped email into Person / Task / Summary."""
    if not email.subject.strip() and not email.body.strip():
        return None

    settings = get_settings()
    completion_kwargs = _completion_kwargs(settings)
    if completion_kwargs.get("api_key") is None:
        logger.error("No API key configured for model %s", settings.litellm_model)
        return None

    try:
        from litellm import acompletion

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(email)},
        ]

        try:
            resp = await acompletion(**completion_kwargs, messages=messages)
        except Exception:
            # Fall back to json_object if this model rejects json_schema.
            if completion_kwargs.get("response_format", {}).get("type") == "json_schema":
                logger.info("Retrying with json_object for %s", settings.litellm_model)
                completion_kwargs["response_format"] = {"type": "json_object"}
                resp = await acompletion(**completion_kwargs, messages=messages)
            else:
                raise
    except Exception:
        logger.exception("LLM classification failed for email %s", email.message_id)
        return None

    content = resp.choices[0].message.content
    if not content:
        return None

    return _parse_classification(content, email)
