Agent memory & backlog

This folder contains lightweight files the local agent and CI workflows use to store short- and long-term context.

Files:
- memory.json — long-term facts (append-only, prune by age)
- backlog.json — prioritized todo items created by the agent
- session_cache/ — transient session transcripts and summaries
- config.yaml — agent configuration (model preferences, cost caps, policies)

Usage:
- Use app/ai/agent_memory.py to read/write memory and backlog from Python code.
- CI jobs can run scripts/agent_sync.py to summarize recent activity and add items to memory/backlog.
