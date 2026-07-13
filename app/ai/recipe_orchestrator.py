import json
from typing import Any, Callable

from loguru import logger

from app.ai.gemini_adapter import generate_text as generate_gemini_text
from app.ai.groq_adapter import generate_text as generate_groq_text
from app.ai.json_utils import extract_json_text
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.fallback_recipe_service import FallbackRecipeService


class RecipeOrchestrator:
    """Generate recipes with configured AI providers and a deterministic local fallback."""

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

        from app.ai.provider_selector import available_providers, select_provider

        selected = select_provider(provider)
        providers = [selected]
        if provider == "auto":
            providers = [candidate for candidate in available_providers() if candidate != "local"]

        generators: dict[str, tuple[Callable[[str], str], str]] = {
            "groq": (generate_groq_text, "groq"),
            "gemini": (generate_gemini_text, "google-gemini"),
        }

        prompt = self._recipe_prompt(request)
        for candidate in providers:
            generator = generators.get(candidate)
            if not generator:
                continue

            generate_text, provider_label = generator
            try:
                text = generate_text(prompt)
                payload: dict[str, Any] = json.loads(extract_json_text(text))
                payload["ai_provider"] = provider_label
                return RecipeResponse.model_validate(payload)
            except Exception as exc:
                logger.warning(
                    "{} generation failed, trying next provider/local fallback: {}",
                    candidate.title(),
                    exc,
                )

        return self.fallback_service.generate(request)

    def _recipe_prompt(self, request: RecipeRequest) -> str:
        """Build a compact prompt to minimize paid input and output tokens."""
        return (
            "Create one balanced recipe. Return JSON with exactly these keys: "
            "title,summary,ingredients,steps,nutrition_estimate,substitutions,safety_review. "
            f"goal={request.goal};servings={request.servings};"
            f"max_carbs={request.max_carbs_per_serving};"
            f"preferences={request.preferences};avoid={request.avoid_ingredients};"
            f"culture={request.culture}. Keep ingredients and steps concise."
        )
