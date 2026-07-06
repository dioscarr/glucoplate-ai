# GlucoPlate AI

AI-powered diabetes-conscious recipe, meal-planning, grocery, and store-assistance system built as a portfolio-grade AI system architecture project.

> **Important:** This project is for education, meal planning support, and software architecture demonstration only. It does not diagnose diabetes, treat medical conditions, adjust medication, or replace guidance from a clinician or registered dietitian.

## Vision

GlucoPlate AI helps users discover diabetes-conscious meals, generate culturally relevant recipes, plan meals, build grocery lists, compare ingredient/product availability, find nearby stores, and understand nutrition tradeoffs through AI-assisted workflows with safety guardrails.

The project is also designed to demonstrate how a modern developer can use AI-assisted engineering in a structured way: clear architecture, API boundaries, agent roles, fallback behavior, safety rules, and developer memory/backlog workflows.

## Why This Project Exists

Many recipe apps generate meals without considering health constraints, cultural food preferences, portioning, product availability, grocery planning, or safety boundaries.

GlucoPlate AI is designed to show how an AI product can combine:

- user-centered product design
- health-aware guardrails
- multi-agent recipe generation
- nutrition review and tradeoff explanation
- culturally relevant food recommendations
- grocery/product lookup workflows
- store discovery and route planning
- image generation support for recipe galleries
- clean Python architecture
- API-first engineering
- AI-assisted development workflows

## Current Status

Active MVP prototype with a working FastAPI backend, static web UI, AI recipe orchestration, grocery/store services, recipe persistence, cart workflows, route planning, image gallery job endpoints, and developer-focused agent memory infrastructure.

## Core Capabilities

### Recipe and Meal Support

- Diabetes-conscious recipe generation
- Meal-planning foundation
- Cultural recipe support
- Ingredient substitutions
- Nutrition estimation
- Safety review and guardrail checks
- Final response review before returning AI output
- Local fallback recipe generation when AI execution fails or is disabled

### Grocery, Store, and Cart Workflows

- Nearby store search
- Product availability/search support
- Ingredient normalization for product lookup
- Saved recipe storage
- Cart creation, listing, lookup, and update endpoints
- Route planning across store stops
- Store enrichment using website metadata when available

### Recipe Image and Gallery Workflows

- Recipe image prompt/schema support
- Recipe gallery job enqueue endpoint
- Gallery polling endpoint
- Static generated-image rendering support

### Developer / Agent Workflow Infrastructure

- Development-only agent interface helpers for Copilot-driven workflows
- Lightweight file-backed short-term and long-term memory
- Backlog storage for agent/planning tasks
- Session transcript persistence
- Redaction helpers for emails, secrets, tokens, UUIDs, and credit-card-like values
- Middleware that can record important POST/PUT API activity into agent memory

## High-Level Product Flow

```text
User Preferences + Health Constraints
        ↓
Recipe Request
        ↓
Planner Agent
        ↓
Recipe Agent
        ↓
Nutrition Agent
        ↓
Safety Agent
        ↓
Reviewer Agent
        ↓
Validated Recipe Response
        ↓
Save Recipe / Generate Images / Build Cart / Search Products / Find Stores / Plan Route
```

## AI Architecture

GlucoPlate AI uses a multi-agent orchestration pattern for recipe generation.

```text
RecipeApplicationService
        ↓
RecipeOrchestrator
        ↓
PlannerAgent
        ↓
RecipeAgent
        ↓
NutritionAgent
        ↓
SafetyAgent
        ↓
ReviewerAgent
        ↓
RecipeResponse
```

The orchestrator coordinates each step and passes structured context forward. If AI execution fails, the system falls back to a local recipe generation service so the app remains demoable and resilient.

## API Surface

The FastAPI backend currently exposes endpoints for:

- `POST /api/recipes/generate` — generate a recipe with optional AI execution
- `POST /api/recipes/gallery` — enqueue recipe image/gallery generation
- `GET /api/recipes/gallery/{job_id}` — poll a gallery job
- `POST /api/recipes/save` — save a generated recipe
- `GET /api/recipes/list` — list saved recipes
- `POST /api/stores/search` — find nearby stores
- `POST /api/stores/enrich` — enrich store data with website metadata
- `POST /api/products/search` — search product availability
- `POST /api/ingredients/normalize` — normalize ingredients into searchable product terms
- `POST /api/carts` — create a cart
- `GET /api/carts` — list carts
- `GET /api/carts/{cart_id}` — get a cart
- `PUT /api/carts/{cart_id}` — update a cart
- `POST /api/route/plan` — plan a route across selected store stops
- `GET /api/ai/health` — check whether the Copilot SDK package is available
- `GET /health` — application health check

## Safety Principles

The system must:

- Avoid medical diagnosis.
- Avoid medication, insulin, or dosage adjustment advice.
- Avoid claims that recipes cure diabetes.
- Flag unsafe recommendations.
- Explain nutrition tradeoffs clearly.
- Encourage professional medical guidance for personal care decisions.
- Prefer conservative safety behavior over overconfident AI output.

## Python Stack

- Python 3.12+
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- SQLite for local development
- PostgreSQL target for production
- Loguru
- GitHub Copilot SDK
- pytest
- httpx
- Ruff

## Repository Structure

```text
app/
  ai/
    agents/
    agent_interface.py
    agent_memory.py
    redaction.py
    recipe_orchestrator.py
  api/
    routes.py
  core/
  models/
  schemas/
  services/
  safety/
  static/
docs/
  product/
  architecture/
  ai-safety/
  data-model/
tests/
.github/
  agent/
```

## What This Project Demonstrates

This project is meant to demonstrate more than a recipe generator. It shows an architecture-first approach to building AI-enabled products:

- defining clear service boundaries
- separating API routes, schemas, services, and AI orchestration
- using specialized agents instead of one monolithic AI call
- validating and reviewing AI output before returning it to the user
- keeping local fallback behavior for reliability
- adding safety constraints for health-adjacent use cases
- supporting product workflows beyond chat, including stores, carts, routes, and generated assets
- creating lightweight memory/backlog infrastructure for AI-assisted development workflows

## Roadmap

Planned improvements:

- Add screenshots and demo GIFs
- Expand architecture documentation
- Add database-backed persistence
- Add authentication and user profiles
- Add stronger nutrition validation against structured food data
- Add automated tests for core services and agent orchestration
- Add CI checks for linting and tests
- Improve production deployment documentation
- Expand safety documentation for health-adjacent AI systems

## Portfolio Positioning

GlucoPlate AI is part of a broader AI Systems Architecture career path. It demonstrates how to take a product idea, define the architecture, create the API and service contracts, introduce agentic workflows, and apply safety constraints so AI-assisted tools and developers can build against a clear technical plan.
