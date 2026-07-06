Long-term context (persisted memory)

Purpose
- Store stable facts, conventions, architecture decisions, and long-lived user preferences.

What belongs here
- Project-wide decisions (APIs, architecture rules, third-party integrations).
- Durable user preferences (e.g., "Prefer Copilot for creative outputs").
- Reusable heuristics and models (e.g., ingredient normalization rules, safety thresholds).

Maintenance
- Periodically pruned by age (config.memory_retention_days).
- Only include facts after a summarization and vetting step (agent_sync or manual review).
- Each entry must cite source (file, commit, or session id).

Format
- Stored programmatically in .github/agent/memory.json via AgentMemory.
- Human-readable summaries live in this markdown for reviewers.
