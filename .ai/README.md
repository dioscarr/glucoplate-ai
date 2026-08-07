# GlucoPlate AI Handoff System

This directory is the human-readable orchestration layer for GitHub Copilot and other coding agents working on GlucoPlate AI.

## Flow

```text
Human objective
    |
    v
Planner
    |
    v
Architect (when boundaries/contracts change)
    |
    v
Implementer
    |
    v
Tester
    |
    v
Reviewer
    |
    v
Memory Keeper
    |
    +----> project-state / decisions
    |
    +----> current handoff ----> next session
```

## Directory map

```text
.ai/
  agents/
    planner.md
    architect.md
    implementer.md
    tester.md
    reviewer.md
    memory-keeper.md
  contracts/
    work-item.md
    implementation-plan.md
    review.md
  handoffs/
    current.md
    TEMPLATE.md
  memory/
    project-state.md
    decisions.md
```

## Operating principle

Agents are allowed to be smart, but they are not allowed to be vague. Each role must leave an artifact that the next role can consume without reconstructing the entire conversation.

The existing `.github/agent/` system remains the programmatic session-memory/backlog layer. This `.ai/` directory is the durable orchestration and handoff layer.
