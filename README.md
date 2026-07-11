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
Save Recipe / Build Cart / Find Products
```

### Primary users

- Home cooks deciding what to make
- Families planning practical meals
- People cooking from ingredients they already own
- Users adapting recipes around preferences or allergies
- Beginners who want clear cooking instructions
- Experienced cooks looking for inspiration across cuisines

## API

### Recipes

- `POST /api/recipes/generate`
- `POST /api/recipes/save`
- `GET /api/recipes/list`
- `POST /api/recipes/recents`
- `GET /api/recipes/recents`
- `POST /api/recipes/gallery`
- `GET /api/recipes/gallery/{job_id}`

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
- Static responsive web UI
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
tests/
.github/
```

## Next MVP Milestones

1. Improve recipe generation quality and structured validation.
2. Add recipe detail and saved-recipe management screens.
3. Add pantry inventory and "cook with what I have" flows.
4. Convert a recipe into a grocery list and cart.
5. Add recipe adjustment actions such as scale servings, substitute an ingredient, change cuisine, and reduce cooking time.
6. Add meal planning after the recipe workflow is stable.
7. Retire or isolate receipt-specific code and tests that are no longer part of the product.
8. Add authentication and database-backed user cookbooks.

## Product Principle

GlucoPlate should help users answer one question quickly:

> What can I cook right now that fits my situation?

Health and nutrition can enhance the answer, but they do not define the audience.
