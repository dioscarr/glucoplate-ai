import json
from typing import Any

from loguru import logger

from app.ai.gemini_adapter import generate_text
from app.ai.json_utils import extract_json_text
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.fallback_recipe_service import FallbackRecipeService


class RecipeOrchestrator:
    """Generate recipes with Gemini and fall back locally when Gemini is unavailable."""

    def __init__(self, fallback_service: FallbackRecipeService | None = None) -> None:
        self.fallback_service = fallback_service or FallbackRecipeService()

    async def generate(
        self,
        request: RecipeRequest,
        use_ai: bool = True,
        provider: str = "auto",
    ) -> RecipeResponse:
        if not use_ai or provider == "local":
            return self.fallback_service.generate(request)

        try:
            return self._generate_with_gemini(request)
        except Exception as exc:
            logger.warning("Gemini generation failed, using local fallback: {}", exc)
            return self.fallback_service.generate(request)

    def _generate_with_gemini(self, request: RecipeRequest) -> RecipeResponse:
        text = generate_text(self._gemini_prompt(request))
        payload: dict[str, Any] = json.loads(extract_json_text(text))
        payload["ai_provider"] = "google-gemini"
        return RecipeResponse.model_validate(payload)

    def _gemini_prompt(self, request: RecipeRequest) -> str:
        return (
            "Create a balanced recipe for a wellness meal planning app. "
            "Return only JSON with keys: title, summary, ingredients, steps, "
            "nutrition_estimate, substitutions, safety_review. "
            f"Goal: {request.goal}. "
            f"Servings: {request.servings}. "
            f"Max carbs per serving: {request.max_carbs_per_serving}. "
            f"Preferences: {request.preferences}. "
            f"Avoid: {request.avoid_ingredients}. "
            f"Style: {request.culture}."
        )
