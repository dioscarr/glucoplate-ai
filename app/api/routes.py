from fastapi import APIRouter, Query

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.recipe_generator import generate_recipe

router = APIRouter(prefix="/api")


@router.post("/recipes/generate", response_model=RecipeResponse)
async def generate_recipe_endpoint(
    request: RecipeRequest,
    use_ai: bool = Query(default=True, description="Use Copilot SDK provider when available."),
) -> RecipeResponse:
    return await generate_recipe(request, use_ai=use_ai)
