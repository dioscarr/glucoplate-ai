from app.schemas.recipe import RecipeRequest
from app.services.fallback_recipe_service import FallbackRecipeService


def test_fallback_recipe_returns_safe_response() -> None:
    service = FallbackRecipeService()
    request = RecipeRequest(goal="Dominican dinner", culture="Dominican")

    response = service.generate(request)

    assert response.title
    assert response.ingredients
    assert response.steps
    assert response.safety_review.disclaimer
    assert response.ai_provider == "local-fallback"
