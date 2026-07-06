# GitHub Copilot Instructions

## Project Identity

GlucoPlate AI is a Python/FastAPI portfolio project demonstrating AI systems architecture for diabetes-friendly recipe and meal planning.

The project should be built as a safe wellness-support system, not as a medical device or clinical decision tool.

## Development Style

When generating code:

- Use Python 3.12+.
- Prefer FastAPI, Pydantic, and typed service classes/functions.
- Keep files small and focused.
- Separate API routes, schemas, services, repositories, safety checks, and AI providers.
- Prefer local JSON data before adding databases.
- Make AI providers swappable through interfaces.
- Do not hard-code API keys.
- Use environment variables for secrets.
- Write code that can run in GitHub Codespaces.

## Architecture Rules

Follow this boundary:

```text
API Route
  -> Application Service
  -> Domain / Safety / Nutrition Services
  -> Repository / JSON Store / External API Provider
```

Do not place business logic directly in FastAPI route functions.

## AI Safety Rules

The application must never:

- Diagnose diabetes.
- Recommend insulin or medication changes.
- Claim that a recipe cures diabetes.
- Encourage extreme fasting or unsafe restriction.
- Provide emergency medical advice.

The application should:

- Explain that nutrition estimates are approximate.
- Encourage clinician or registered dietitian review for personal medical decisions.
- Flag unsafe prompts and risky recipe outputs.
- Prefer balanced meals with protein, fiber, vegetables, and controlled carbohydrates.

## Recipe Generation Rules

Generated recipes should include:

- Title
- Summary
- Ingredients
- Steps
- Nutrition estimate
- Substitutions
- Safety review

## Copilot Task Pattern

When implementing a new feature, use this pattern:

1. Update or create the Pydantic schema.
2. Add service logic.
3. Add JSON repository support if needed.
4. Add API route.
5. Add tests.
6. Update docs.

## Preferred Commit Style

Use concise feature-oriented messages, for example:

- `Add local recipe repository`
- `Add AI provider interface`
- `Add nutrition safety checks`
- `Add Codespaces configuration`

---

# Copilot CLI / Agent Wiring (development-only)

Purpose
- These instructions guide Copilot CLI-driven automation and local chat agents that operate on this repository for development tasks. They explain how to load context, update agent memory/backlog files, and apply safety/cost gates.

Key development-only files (agent helpers)
- .github/agent/soul.md — guiding principles (safety, cost, provenance)
- .github/agent/config.yaml — model preferences, cost caps, and approval thresholds
- .github/agent/longterm-context.md — rules for durable facts
- .github/agent/shortterm-context.md — session cache rules
- .github/agent/backlog.md — backlog conventions

Programmatic helpers (use from scripts or Copilot CLI)
- app.ai.agent_interface.load_context_for_session(session_id)
  - Returns {long_term: [...], short_term: [...], config: ...}
- app.ai.agent_interface.append_session_transcript(session_id, transcript_text)
  - Save redacted transcripts to .github/agent/session_cache/
- app.ai.agent_interface.persist_session_summary(session_id, summary, tags=None)
  - Persist vetted summaries to long-term memory
- app.ai.agent_memory.AgentMemory
  - list_memory(), add_memory(fact, tags), list_backlog(), add_backlog(title, details)

Behavior rules for Copilot-driven agents
1. Load context at session start
   - Call load_context_for_session(session_id) and include its long_term and short_term summaries in the system prompt.
2. Redact before writing
   - Never write secrets, API keys, or unredacted PII to session_cache or memory.json. Use provided redaction helpers or refuse.
3. Short-term vs long-term writes
   - Append raw session transcripts to session_cache via append_session_transcript().
   - Persist only short vetted summaries to long-term memory via persist_session_summary().
4. Cost & human approval
   - Respect .github/agent/config.yaml human_approval_threshold_usd. If an operation (e.g., high-cost image generation) exceeds the threshold, request explicit human approval before proceeding.
5. Safety
   - Do not provide medical diagnoses, dosing advice, or emergency instructions. For risky prompts, return a safe fallback and recommend clinician review.
6. Backlog
   - When a work item is identified, call AgentMemory.add_backlog(title, details) with tags and provenance.
7. Traceability
   - Memory/backlog entries must include provenance: session_id, source, and timestamp.

Prompt guidance
- System prompt: include up to 8 top long-term facts and 6 most recent short-term filenames with concise metadata.
- Keep summaries compact; use a cheap summarizer for long transcripts when available.

Operational notes
- These helpers are for local development agents only and must not be exposed as public HTTP endpoints.
- CI may run scripts/agent_sync.py to summarize session cache periodically.

Example pseudo-flow
- At start: ctx = load_context_for_session(session_id)
  Build system prompt with ctx['long_term'][:8] and ctx['short_term'][:6]
- After output: safe = redact_secrets(transcript)
  append_session_transcript(session_id, safe)
  summary = summarize_short(safe)
  persist_session_summary(session_id, summary, tags=['auto-summary'])

If unsure about safety or cost, stop and ask for human confirmation.


