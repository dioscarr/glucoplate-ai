"""Redaction helpers for development-only agent transcripts.

Provides simple, conservative redaction utilities that Copilot CLI agents should use
before persisting transcripts to session_cache or long-term memory.

Note: These helpers are intentionally simple for development use. They are not a
substitute for a formal PII/secret detection pipeline in production.
"""
from __future__ import annotations
import re
from typing import Tuple

# Patterns to redact (conservative; prefer false positives to leaking secrets)
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}")
API_KEY_RE = re.compile(r"(?:api[_-]?key|secret|token)[\s:=]+[A-Za-z0-9._\-]{8,}", re.IGNORECASE)
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
# Basic credit card-ish pattern (very coarse)
CC_RE = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")

REPLACEMENTS = [
    (EMAIL_RE, "[REDACTED_EMAIL]"),
    (API_KEY_RE, "[REDACTED_SECRET]"),
    (UUID_RE, "[REDACTED_ID]"),
    (CC_RE, "[REDACTED_CC]")
]


def redact_text(text: str) -> Tuple[str, int]:
    """Return (redacted_text, count_of_replacements).

    Replaces matches for known patterns with conservative placeholders.
    """
    count = 0
    out = text
    for pat, repl in REPLACEMENTS:
        out, n = pat.subn(repl, out)
        count += n
    return out, count


def redact_json_like(text: str) -> Tuple[str, int]:
    """Attempt to redact JSON-ish payloads by removing values for keys like api_key, token, secret.

    This searches for simple key: value patterns and replaces the value with [REDACTED_SECRET].
    """
    # key: "value" or 'value' or key: value
    key_re = re.compile(r"\b(api_key|apikey|secret|token|password)\b\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,\n\r]+)", re.IGNORECASE)
    out, n = key_re.subn(lambda m: m.group(0).split(':')[0] + ': [REDACTED_SECRET]', text)
    return out, n


if __name__ == "__main__":
    sample = "User email: me@example.com, api_key=sk_test_1234567890abcdef"
    print(redact_text(sample))
    print(redact_json_like('{"api_key": "sk_test_123"}'))
