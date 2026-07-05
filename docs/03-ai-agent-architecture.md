# AI Agent Architecture

## Purpose

The agent layer demonstrates how to split an AI task into focused responsibilities instead of relying on one large prompt.

## Agents

### Planner Agent

Converts the user request into a recipe strategy.

### Recipe Agent

Creates the draft recipe using the plan and local knowledge.

### Nutrition Agent

Reviews macronutrient targets and identifies nutrition concerns.

### Safety Agent

Checks for unsafe claims, medication advice, or risky recommendations.

### Reviewer Agent

Validates the final response shape and consistency before returning to the API.

## Workflow

```text
RecipeRequest
  -> Planner Agent
  -> Recipe Agent
  -> Nutrition Agent
  -> Safety Agent
  -> Reviewer Agent
  -> RecipeResponse
```

## Runtime Provider

The first AI runtime target is the GitHub Copilot SDK Python cookbook pattern.

The application keeps this dependency isolated so it can:

- run in Codespaces with Copilot support,
- run locally in fallback mode,
- add additional providers later without changing API contracts.

## Structured Output

Agents should return JSON or strongly typed Pydantic models whenever possible. Free-form text should stay at the edges of the system.
