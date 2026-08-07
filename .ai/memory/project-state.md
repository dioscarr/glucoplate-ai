# GlucoPlate AI Project State

Last reviewed: 2026-08-06

## Product
GlucoPlate AI is an AI-powered recipe companion for people deciding what to cook from ingredients, preferences, culture, time, and cooking goals. Nutrition is a supporting personalization surface, not the primary product positioning.

## Current MVP capabilities
- natural-language recipe generation
- servings, cuisine/culture, preferences, avoided ingredients, and optional nutrition targets
- ingredients, steps, substitutions, and estimated nutrition
- saved cookbook and recent recipes
- ingredient normalization
- store/product search
- carts and route planning
- recipe gallery jobs
- AI provider abstraction with local fallback
- cuisine/popular recipe browsing
- Firebase push notification support

## Stack
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite locally; PostgreSQL production target
- GitHub Copilot SDK / Gemini provider abstraction
- responsive static PWA UI
- Firebase Cloud Messaging
- pytest, httpx, Ruff

## Repository architecture
Primary application areas live under `app/` including AI, API, core, models, schemas, services, safety, and static UI assets. Documentation lives under `docs/`; milestones under `milestones/`; tests under `tests/`.

## Agent system
- `.github/agent/` is the existing programmatic agent memory/backlog layer.
- `.ai/` is the human-readable orchestration layer for roles, contracts, project state, architectural decisions, and session handoffs.
- `.github/copilot-instructions.md` is the root operating contract for Copilot agents.

## Current engineering direction
The repository roadmap currently emphasizes native iOS/PWA polish, authentication/cloud-backed accounts, personalization, meal planning/grocery lists, collaboration, step-aware cooking assistance, and production readiness.

## Known orchestration gap
The handoff system is convention-driven. CI or tooling does not yet enforce that required handoff/memory artifacts are updated before a change is considered complete.
