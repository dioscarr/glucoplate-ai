from app.ai.redaction import redact_text, redact_json_like


def test_redact_text_email_and_api_key():
    text = "Contact: dev@example.com, api_key=sk_test_1234567890abcdef"
    redacted, count = redact_text(text)
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_SECRET]" in redacted
    assert count >= 2


def test_redact_json_like():
    text = '{"api_key": "sk_live_abcdef"}'
    out, n = redact_json_like(text)
    assert 'REDACTED_SECRET' in out
    assert n >= 1
