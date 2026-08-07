# GitHub Copilot Instructions

## Project Identity

GlucoPlate AI is an AI-powered recipe companion that helps people decide what to cook from their ingredients, preferences, culture, time, and cooking goals. Nutrition and dietary preferences support personalization, but the product is not positioned as a medical device or clinical decision tool.

## Development Style

When generating code:

- Use Python 3.12+.
- Prefer FastAPI, Pydantic, SQLAlchemy, and typed service classes/functions.
- Keep files small and focused.
- Separate API routes, schemas, services, repositories, safety checks, and AI providers.
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
  -> Repository / Data Store / External API Provider
```

Do not place business logic directly in FastAPI route functions.

## AI Safety Rules

The application must never diagnose a user, recommend medication changes, make cure claims, encourage dangerous restriction, or present nutrition estimates as exact clinical guidance.

The application should clearly communicate uncertainty, keep AI providers behind interfaces, validate structured output, fail safely, and preserve a local fallback where supported.

## Recipe Generation Rules

Generated recipes should include the fields expected by the active schemas and API contracts, including title, summary, ingredients, steps, nutrition estimates, substitutions, and applicable safety or review metadata.

## Copilot Handoff Operating System

Treat this repository as a coordinated multi-agent engineering system, not a collection of isolated prompts.

For meaningful work, follow this pipeline:

1. Understand the objective and current state.
2. Plan the smallest coherent slice.
3. Define architecture/contracts when the change crosses boundaries.
4. Implement the slice.
5. Verify with tests and repository checks.
6. Review the total change for regressions, security, safety, and product fit.
7. Update durable memory and leave a precise handoff for the next session.

### Context to load

Read these files when relevant before making meaningful changes:

- `README.md`
- `PROJECT_STATUS.md`
- `ROADMAP.md`
- `docs/AI_DEVELOPMENT_GUIDE.md`
- `.ai/memory/project-state.md`
- `.ai/memory/decisions.md`
- `.ai/handoffs/current.md`
- `.github/agent/` when using the existing programmatic agent-memory helpers

### Role routing

Use the prompts in `.ai/agents/` as explicit modes:

- `planner.md` — converts objectives into executable plans.
- `architect.md` — defines boundaries, contracts, data flow, and tradeoffs.
- `implementer.md` — implements an approved slice with minimal scope.
- `tester.md` — verifies behavior, edge cases, and regressions.
- `reviewer.md` — reviews the whole change before merge.
- `memory-keeper.md` — records durable state and prepares the next handoff.

One Copilot session may perform several roles, but it must keep role transitions explicit and respect the output contract of each role.

### Rules of engagement

- Do not invent requirements unsupported by the repo, user request, or recorded decisions.
- Prefer small, reviewable changes over broad rewrites.
- Preserve existing behavior unless the objective changes it.
- Do not code across an architectural boundary until the contract is clear enough to test.
- Add or update tests for behavior changes.
- Run the narrowest useful checks first, then broader checks when warranted.
- For user-facing changes, consider API, PWA/UI, accessibility, loading/error states, and observability.
- For AI changes, consider provider failure, fallback behavior, structured output validation, safety, and cost.
- For data changes, consider migrations and production PostgreSQL even when SQLite is used locally.
- Never mark work complete with known blockers hidden. Record them in the handoff.

### Handoff contract

At the end of meaningful work, update `.ai/handoffs/current.md` with:

- objective
- current status
- what changed
- files touched
- validation performed
- decisions made
- unresolved risks/blockers
- exact recommended next action

If work changes durable understanding of the project, also update `.ai/memory/project-state.md` and/or `.ai/memory/decisions.md`.

### Definition of done

Work is complete only when the requested behavior or analysis is complete, relevant checks pass or failures are documented, no known critical regression is left unaddressed, and the handoff is updated.

## Existing Agent Memory Integration

The repository already includes development-only agent helpers under `.github/agent/` and `app.ai.agent_interface`. Keep using them where programmatic session memory is appropriate.

Key development-only files:

- `.github/agent/soul.md`
- `.github/agent/config.yaml`
- `.github/agent/longterm-context.md`
- `.github/agent/shortterm-context.md`
- `.github/agent/backlog.md`

Programmatic helpers:

- `app.ai.agent_interface.load_context_for_session(session_id)`
- `app.ai.agent_interface.append_session_transcript(session_id, transcript_text)`
- `app.ai.agent_interface.persist_session_summary(session_id, summary, tags=None)`
- `app.ai.agent_memory.AgentMemory`

Use `.github/agent/` for programmatic session cache/backlog memory and `.ai/` for human-readable orchestration, role contracts, project state, and handoffs. Never write secrets, API keys, or unredacted PII to either system.
