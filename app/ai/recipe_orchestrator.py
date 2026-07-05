from app.ai.copilot_recipe_provider import CopilotRecipeProvider
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.fallback_recipe_service import FallbackRecipeService


class RecipeOrchestrator:
    """Coordinates AI-first generation with local fallback support."""

    def __init__(
        self,
        copilot_provider: CopilotRecipeProvider | None = None,
        fallback_service: FallbackRecipeService | None = None,
    ) -> None:
        self.copilot_provider = copilot_provider or CopilotRecipeProvider()
        self.fallback_service = fallback_service or FallbackRecipeService()

    async def generate(self, request: RecipeRequest, use_ai: bool = True) -> RecipeResponse:
        if not use_ai:
            return self.fallback_service.generate(request)

        try:
            return await self.copilot_provider.generate(request)
        except Exception:
            # MVP behavior: fallback keeps the demo deployable even without Copilot SDK runtime.
            # Production behavior should log this exception and expose diagnostic metadata safely.
            return self.fallback_service.generate(request)
