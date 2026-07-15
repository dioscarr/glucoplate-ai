# ADR-001: Documentation and Milestone Structure

## Status

Accepted

## Context

GlucoPlate AI is growing across recipe generation, Firebase notifications, PWA behavior, mobile-native features, authentication, meal planning, shopping, and AI personalization. The project needs a lightweight structure that keeps product intent, implementation tasks, and release planning visible.

## Decision

Use two top-level planning areas:

- `docs/` for durable product, architecture, development, deployment, and integration documentation.
- `milestones/` for release-oriented execution plans and task checklists.

Add root-level summary files:

- `PROJECT_STATUS.md` for the current live snapshot.
- `ROADMAP.md` for release sequence.
- `CHANGELOG.md` for human-readable history.

## Consequences

- Every meaningful feature should update a milestone file.
- PRs should reference the milestone they advance.
- Contributors and coding agents can find the product direction without reading the entire repository.
- Documentation must be maintained as product code evolves.
