# GlucoPlate AI Decisions

Record durable decisions here. Keep entries concise and append-only unless a later decision explicitly supersedes an earlier one.

## 2026-08-06 — Split agent memory from orchestration memory

**Decision:** Keep `.github/agent/` as the programmatic session-memory/backlog layer and introduce `.ai/` as the human-readable orchestration layer.

**Why:** The repository already has code and conventions around `.github/agent/`. Replacing it would create unnecessary migration risk. The new handoff system needs clearer role contracts and durable project context that humans can inspect directly.

**Implication:** Agents should load both systems when relevant. Session transcripts and programmatic backlog state belong in `.github/agent/`; roles, work contracts, project state, decisions, and handoffs belong in `.ai/`.

## 2026-08-06 — Require a handoff after meaningful work

**Decision:** Meaningful agent work must end by updating `.ai/handoffs/current.md`.

**Why:** A concrete handoff prevents the next Copilot session from reconstructing objectives, validation, blockers, and next steps from git history or chat context alone.

**Implication:** The handoff is part of the definition of done, even when no durable architectural decision was made.

## 2026-08-06 — Use explicit role boundaries without requiring separate processes

**Decision:** Planner, Architect, Implementer, Tester, Reviewer, and Memory Keeper are explicit role contracts, but one Copilot session may execute multiple roles sequentially.

**Why:** This gets the quality benefits of handoff discipline without requiring external multi-agent infrastructure on day one.

**Implication:** Role transitions should be explicit and each role should produce the artifact expected by the next stage.
