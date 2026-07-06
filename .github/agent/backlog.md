Agent Backlog (brief)

Purpose
- Record prioritized tasks, suggestions, and follow-ups the agent has identified.
- Feed for human review and triage.

Example entries
- "Improve product-store fuzzy matching using Fuse.js" — suggested after numerous unmatched product->store lookups.
- "Add background image job queue" — implemented (gallery_job_service). Consider retries.

Workflow
- Agent adds backlog items via app/ai/agent_memory.py (add_backlog).
- Humans review backlog.md periodically and convert items into issues/PRs.
- Backlog entries in backlog.json are the authoritative source for programmatic access.
