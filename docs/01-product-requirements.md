# Product Requirements

## Product

GlucoPlate AI is an AI-powered diabetes-conscious recipe and meal-planning assistant.

## Goal

Help users generate balanced recipes, meal ideas, and grocery support while keeping safety boundaries clear.

## Target Users

- People looking for diabetes-conscious meal ideas
- Families cooking for someone managing blood sugar
- Developers studying AI systems architecture
- Recruiters/hiring managers reviewing an AI architecture portfolio project

## MVP Features

1. Generate a recipe from a user goal.
2. Use local JSON data for recipe and ingredient knowledge.
3. Run recipe output through nutrition review.
4. Run recipe output through safety review.
5. Return structured JSON through a FastAPI endpoint.
6. Support GitHub Copilot SDK as the AI runtime provider.
7. Provide fallback behavior when AI runtime is unavailable.

## Non-Goals

- Medical diagnosis
- Medication advice
- Insulin adjustment
- Clinical treatment recommendations
- Replacing a clinician or registered dietitian

## Success Criteria

- App runs locally and in GitHub Codespaces.
- API returns valid structured recipe JSON.
- Safety layer always includes a disclaimer.
- AI provider is isolated behind a service boundary.
- Local JSON storage works without a database.
