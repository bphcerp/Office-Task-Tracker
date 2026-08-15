"""LLM agent classification.

Boilerplate only. `classify_email` is a stub returning a structured result
without calling any model, so the pipeline runs before a provider is wired up.
Use LiteLLM's `completion` with `settings.litellm_model` and a JSON schema
prompt to extract Person / Task / Summary here.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.mail import ScrapedEmail


@dataclass
class Classification:
    """Structured output produced by the agent for a single email."""

    person_name: str
    person_email: str | None
    task_title: str
    summary: str


async def classify_email(email: ScrapedEmail) -> Classification | None:
    """Classify a scraped email into Person / Task / Summary.

    TODO(integration): call the LiteLLM model with a prompt that instructs it
    to return strict JSON matching `Classification`. Validate and return None
    on failure / empty input.
    """
    # Example litellm usage (kept commented until a key is configured):
    #
    # from litellm import acompletion
    # from app.config import get_settings
    #
    # settings = get_settings()
    # resp = await acompletion(
    #     model=settings.litellm_model,
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": (
    #                 "Classify the office email into JSON with keys "
    #                 "person_name, person_email, task_title, summary."
    #             ),
    #         },
    #         {"role": "user", "content": email.body},
    #     ],
    # )
    # ...
    return None
