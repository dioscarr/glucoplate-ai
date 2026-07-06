"""Example Copilot CLI session script

Usage: run locally during development to simulate a Copilot-driven session flow.
This script demonstrates how an automated Copilot workflow should:
 - load short-term and long-term context
 - run an AI prompt (placeholder) using that context
 - save the raw transcript to session cache
 - produce a short summary and persist it to long-term memory

Note: Replace the `run_copilot_prompt` placeholder with a real Copilot SDK call in your environment.
"""
import json
import os
import re
import uuid
from datetime import datetime

from app.ai.agent_interface import load_context_for_session, append_session_transcript, persist_session_summary


def redact_secrets(text: str) -> str:
    # very simple redaction: emails, keys that look like API keys
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    text = re.sub(r"(AIza[0-9A-Za-z-_]{35})", "[REDACTED_API_KEY]", text)
    text = re.sub(r"(sk_live_[0-9a-zA-Z]{24,})", "[REDACTED_SK]", text)
    return text


def run_copilot_prompt(prompt: str) -> str:
    """Placeholder for Copilot SDK invocation.
    Replace this with an actual Copilot call, e.g. copilot.run(prompt) or equivalent.
    For demo, it returns a deterministic fake response.
    """
    response = f"FAKE_RESPONSE for prompt (len={len(prompt)}) -- generated at {datetime.utcnow().isoformat()}"
    return response


def main():
    session_id = f"local-{uuid.uuid4().hex[:8]}"
    print('Session id:', session_id)

    # 1) load context
    ctx = load_context_for_session(session_id)
    long_term = ctx.get('long_term', [])
    short_term = ctx.get('short_term', [])
    cfg = ctx.get('config')

    # Prepare prompt for Copilot (keep it small and focused)
    prompt = {
        'instruction': 'Summarize recent work and suggest a single next action (short).',
        'long_term_facts': [m.get('fact') for m in long_term[:8]],
        'recent_sessions': short_term[:6],
    }
    prompt_text = json.dumps(prompt, indent=2)
    print('Prepared prompt (truncated):', prompt_text[:1000])

    # 2) run Copilot prompt (placeholder)
    ai_response = run_copilot_prompt(prompt_text)

    # 3) save raw transcript (redacted) to short-term session cache
    transcript = 'User: run quick dev session\nAI: ' + ai_response
    safe_transcript = redact_secrets(transcript)
    fname = append_session_transcript(session_id, safe_transcript)
    print('Saved session transcript to', fname)

    # 4) generate a short summary and persist to long-term memory
    # In real runs, you would call a cheap summarizer model here
    summary = ai_response[:500]
    summary = redact_secrets(summary)
    mem = persist_session_summary(session_id, summary)
    print('Persisted summary id:', mem.get('id'))

    print('Done')


if __name__ == '__main__':
    main()
