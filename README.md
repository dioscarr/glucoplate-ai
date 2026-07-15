# GlucoPlate AI

**Cook smarter with AI.**

GlucoPlate AI is an AI-powered recipe companion that helps people create meals from their ingredients, preferences, culture, available time, and cooking goals.

The product is a general recipe app. Nutrition information and optional dietary preferences support personalization, but diabetes is not the product's primary audience or positioning.

## Current MVP

- Generate complete recipes from a natural-language request
- Set servings, cuisine or culture, preferences, and avoided ingredients
- Use an optional nutrition target without requiring a medical profile
- Receive ingredients, cooking steps, substitutions, and estimated nutrition
- Save generated recipes to a personal cookbook
- View recent recipes
- Normalize ingredient lists
- Search stores and products
- Create carts and plan shopping routes
- Generate recipe gallery jobs
- Use AI providers when available with a local fallback
- Browse cuisines and popular recipe names
- Enable Firebase push notifications and send test notifications

## Product Direction

The core experience is:

```text
Craving / Ingredients / Cooking Goal
        ↓
Recipe Request
        ↓
AI Provider Selection
        ↓
Recipe Generation and Review
        ↓
Ingredients + Steps + Nutrition + Substitutions
        ↓
Save Recipe / Build Cart / Find Products / Cook Step by Step
```

### Primary users

- Home cooks deciding what to make
- Families planning practical meals
- People cooking from ingredients they already own
- Users adapting recipes around preferences or allergies
- Beginners who want clear cooking instructions
- Experienced cooks looking for inspiration across cuisines

## Documentation and planning

- [Documentation hub](docs/README.md)
- [Project documentation](docs/PROJECT_DOCUMENTATION.md)
- [iOS and PWA native capabilities](docs/IOS_PWA_NATIVE_CAPABILITIES.md)
- [AI development guide](docs/AI_DEVELOPMENT_GUIDE.md)
- [Milestones](milestones/README.md)
- [Project status](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## API

### Recipes

- `POST /api/recipes/generate`
- `POST /api/recipes/save`
- `GET /api/recipes/list`
- `POST /api/recipes/recents`
- `GET /api/recipes/recents`
- `POST /api/recipes/gallery`
- `GET /api/recipes/gallery/{job_id}`

### Push notifications

- `GET /api/push/config`
- `POST /api/push/tokens`
- `DELETE /api/push/tokens`
- `POST /api/push/test`
- `POST /api/push/send`

### Supporting cooking and shopping workflows

- `POST /api/ingredients/normalize`
- `POST /api/products/search`
- `POST /api/stores/search`
- `POST /api/stores/enrich`
- `POST /api/carts`
- `GET /api/carts`
- `POST /api/route/plan`
- `GET /api/ai/health`
- `GET /health`

## Stack

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite locally with PostgreSQL as the production target
- GitHub Copilot SDK / Gemini provider abstraction
- Local fallback recipe generation
- Static responsive PWA UI
- Firebase Cloud Messaging
- pytest, httpx, Ruff

## Repository Structure

```text
app/
  ai/
  api/
  core/
  models/
  schemas/
  services/
  safety/
  static/
docs/
  decisions/
milestones/
tests/
.github/
```

## Next MVP Milestones

1. Native iOS/PWA polish and device capability layer.
2. Firebase Authentication and cloud-backed user accounts.
3. AI personalization from user food profiles and cooking history.
4. Meal planning and grocery list generation.
5. Social sharing and household collaboration.
6. Step-aware AI cooking assistant.
7. Production readiness and launch operations.

## Product Principle

GlucoPlate should help users answer one question quickly:

> What can I cook right now that fits my situation?

Health and nutrition can enhance the answer, but they do not define the audience.
