from __future__ import annotations

import importlib
from typing import Any

from loguru import logger

from app.core.secrets import get_secret

_DEFAULT_MODEL = "llama-3.1-8b-instant"
_DEFAULT_MAX_TOKENS = 420


def generate_text(prompt: str) -> str:
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Groq API key is not configured")

    model = get_secret("GROQ_MODEL") or _DEFAULT_MODEL
    module = importlib.import_module("groq")
    client = module.Groq(api_key=api_key)

    response: Any = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Return only compact valid JSON. No markdown or explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_completion_tokens=_DEFAULT_MAX_TOKENS,
        response_format={"type": "json_object"},
    )

    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "Groq token usage — prompt={}, completion={}, total={}",
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(usage, "total_tokens", None),
        )

    return response.choices[0].message.content or ""
