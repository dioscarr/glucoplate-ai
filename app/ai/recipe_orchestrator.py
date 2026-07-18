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

        from app.ai.provider_selector import select_provider

        selected = select_provider(provider)
        providers = [selected] if selected != "local" else []

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
                payload = self._normalize_payload(payload)
                payload["ai_provider"] = provider_label
                return RecipeResponse.model_validate(payload)
            except Exception as exc:
                logger.warning(
                    "{} generation failed, using local fallback: {}",
                    candidate.title(),
                    exc,
                )

        return self.fallback_service.generate(request)

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        substitutions = payload.get("substitutions")
        if isinstance(substitutions, dict):
            payload["substitutions"] = [
                f"{ingredient}: {replacement}"
                for ingredient, replacement in substitutions.items()
            ]
        elif substitutions is None:
            payload["substitutions"] = []

        safety_review = payload.get("safety_review")
        if not isinstance(safety_review, dict):
            safety_review = {}

        warnings = safety_review.get("warnings")
        if not isinstance(warnings, list):
            warnings = []

        allergens = safety_review.get("allergens")
        if isinstance(allergens, list):
            warnings.extend(f"Allergen: {allergen}" for allergen in allergens)

        notes = safety_review.get("notes")
        if isinstance(notes, list):
            warnings.extend(str(note) for note in notes)

        safety_review["warnings"] = list(dict.fromkeys(str(item) for item in warnings))
        safety_review.setdefault("approved", not safety_review["warnings"])
        safety_review.setdefault(
            "disclaimer",
            "Nutrition values are estimates. Confirm ingredients and dietary needs before serving.",
        )
        payload["safety_review"] = safety_review
        return payload

    def _recipe_prompt(self, request: RecipeRequest) -> str:
        """Build a compact prompt to minimize paid input and output tokens."""
        pantry = request.pantry_items[:80]
        use_soon = request.use_soon_ingredients[:30]
        pantry_instruction = (
            "Prefer ingredients from pantry, prioritize use-soon items, and suggest pantry substitutions "
            "before introducing new purchases. Never assume an ingredient is available unless listed. "
            if pantry
            else ""
        )
        return (
            "Create one balanced recipe. Return compact JSON only with this exact shape: "
            '{"title":"str","summary":"str","ingredients":["str"],'
            '"steps":["str"],"nutrition_estimate":{"calories":0,"protein_g":0,'
            '"carbs_g":0,"fiber_g":0,"sugar_g":0,"fat_g":0,"sodium_mg":0},'
            '"substitutions":["str"],"safety_review":{"approved":true,'
            '"warnings":["str"],"disclaimer":"str"}}. '
            f"{pantry_instruction}"
            f"goal={request.goal};servings={request.servings};"
            f"max_carbs={request.max_carbs_per_serving};"
            f"preferences={request.preferences};avoid={request.avoid_ingredients};"
            f"culture={request.culture};pantry={pantry};use_soon={use_soon}. "
            "Keep ingredients and steps concise."
        )
