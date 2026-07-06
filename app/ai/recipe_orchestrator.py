import json
from typing import Any

from app.ai.agents.nutrition_agent import NutritionAgent
from app.ai.agents.planner_agent import PlannerAgent
from app.ai.agents.recipe_agent import RecipeAgent
from app.ai.agents.reviewer_agent import ReviewerAgent
from app.ai.agents.safety_agent import SafetyAgent
from app.ai.gemini_adapter import generate_text
from app.ai.json_utils import extract_json_text
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.fallback_recipe_service import FallbackRecipeService


class RecipeOrchestrator:
    """Coordinates AI generation with local fallback support."""

    def __init__(
        self,
        planner_agent: PlannerAgent | None = None,
        recipe_agent: RecipeAgent | None = None,
        nutrition_agent: NutritionAgent | None = None,
        safety_agent: SafetyAgent | None = None,
        reviewer_agent: ReviewerAgent | None = None,
        fallback_service: FallbackRecipeService | None = None,
    ) -> None:
        self.planner_agent = planner_agent or PlannerAgent()
        self.recipe_agent = recipe_agent or RecipeAgent()
        self.nutrition_agent = nutrition_agent or NutritionAgent()
        self.safety_agent = safety_agent or SafetyAgent()
        self.reviewer_agent = reviewer_agent or ReviewerAgent()
        self.fallback_service = fallback_service or FallbackRecipeService()

    async def generate(
        self,
        request: RecipeRequest,
        use_ai: bool = True,
        provider: str = "auto",
    ) -> RecipeResponse:
        if not use_ai or provider == "local":
            return self.fallback_service.generate(request)

        if provider in ("auto", "gemini"):
            try:
                return self._generate_with_gemini(request)
            except Exception as exc:
                from loguru import logger

                logger.warning("Gemini generation failed: {}", exc)
                if provider == "gemini":
                    return self.fallback_service.generate(request)

        try:
            request_context = request.model_dump_json(indent=2)
            plan = await self.planner_agent.run(request_context)
            draft_recipe = await self.recipe_agent.run(
                self._to_context({"request": request.model_dump(), "plan": plan})
            )
            nutrition = await self.nutrition_agent.run(
                self._to_context(
                    {
                        "request": request.model_dump(),
                        "plan": plan,
                        "draft_recipe": draft_recipe,
                    }
                )
            )
            safety = await self.safety_agent.run(
                self._to_context(
                    {
                        "request": request.model_dump(),
                        "plan": plan,
                        "draft_recipe": draft_recipe,
                        "nutrition": nutrition,
                    }
                )
            )
            final_response = await self.reviewer_agent.run(
                self._to_context(
                    {
                        "request": request.model_dump(),
                        "plan": plan,
                        "draft_recipe": draft_recipe,
                        "nutrition": nutrition,
                        "safety": safety,
                    }
                )
            )

            payload: dict[str, Any] = json.loads(extract_json_text(final_response))
            payload["ai_provider"] = "github-copilot-sdk-agent-chain"
            return RecipeResponse.model_validate(payload)
        except Exception as exc:
            from loguru import logger

            logger.warning("AI generation failed, using local fallback: {}", exc)
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

    def _to_context(self, value: dict[str, Any]) -> str:
        return json.dumps(value, indent=2, default=str)
