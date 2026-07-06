"""Helpers for extracting JSON from AI model responses.

Copilot/LLM responses often wrap JSON in markdown code fences (```json ... ```)
even when the prompt explicitly asks for raw JSON. These helpers make parsing
resilient to that behavior.
"""

import re

_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json_text(raw_content: str) -> str:
    """Strip markdown code fences and surrounding whitespace from a model response."""
    content = raw_content.strip()
    match = _FENCE_PATTERN.search(content)
    if match:
        content = match.group(1).strip()
    return content
