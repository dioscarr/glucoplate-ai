Short-term context (session cache)

Purpose
- Keep recent session transcripts, prompts, and temporary state useful for immediate follow-ups.

Characteristics
- Ephemeral: retained for a short window (config.short_term_window_days) and then summarized or purged.
- Lightweight: compact summaries rather than full transcripts when possible.
- Used by the agent during active sessions to maintain continuity.

Storage
- session_cache/*.json files (created by the app or agent sync scripts).
- Periodic summarization consolidates these into long-term facts when appropriate.

Privacy
- Do not store secrets or PII in short-term context. Redact any sensitive fields before writing.
