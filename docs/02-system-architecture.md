# System Architecture

## Architecture Style

GlucoPlate AI uses a layered architecture with AI orchestration separated from API routes and domain logic.

```text
FastAPI Routes
  -> Application Services
  -> AI Orchestrator
  -> AI Agents
  -> Domain Services
  -> JSON Repositories
  -> Local JSON Data
```

## Layers

### API Layer

Receives HTTP requests and returns Pydantic response models.

### Application Layer

Coordinates user-facing use cases such as recipe generation.

### AI Orchestration Layer

Runs the multi-agent workflow:

1. Planner Agent
2. Recipe Agent
3. Nutrition Agent
4. Safety Agent
5. Reviewer Agent

### Domain Layer

Contains nutrition and safety logic independent of FastAPI and Copilot.

### Persistence Layer

Uses local JSON files for the MVP. This keeps the project cheap, portable, and deployable in Codespaces.

## Data Flow

```text
RecipeRequest
  -> RecipeApplicationService
  -> RecipeOrchestrator
  -> PlannerAgent
  -> RecipeAgent
  -> NutritionAgent
  -> SafetyAgent
  -> ReviewerAgent
  -> RecipeResponse
```

## Provider Strategy

The Copilot SDK is isolated behind `CopilotAgentClient` and agent classes. The application can fall back to deterministic local generation if the SDK is unavailable.
