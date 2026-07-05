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
