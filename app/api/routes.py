from fastapi import APIRouter

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.recipe_generator import generate_recipe

router = APIRouter(prefix="/api")


@router.post("/recipes/generate", response_model=RecipeResponse)
def generate_recipe_endpoint(request: RecipeRequest) -> RecipeResponse:
    return generate_recipe(request)
