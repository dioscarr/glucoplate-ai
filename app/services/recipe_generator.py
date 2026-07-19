from app.ai.recipe_orchestrator import RecipeOrchestrator
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.pantry_coverage_service import PantryCoverageService


class RecipeApplicationService:
    def __init__(
        self,
        orchestrator: RecipeOrchestrator | None = None,
        pantry_coverage_service: PantryCoverageService | None = None,
    ) -> None:
        self.orchestrator = orchestrator or RecipeOrchestrator()
        self.pantry_coverage_service = pantry_coverage_service or PantryCoverageService()

    async def generate_recipe(
        self,
        request: RecipeRequest,
        use_ai: bool = True,
        provider: str = "auto",
    ) -> RecipeResponse:
        recipe = await self.orchestrator.generate(request, use_ai=use_ai, provider=provider)
        coverage = self.pantry_coverage_service.analyze(
            recipe.ingredients,
            request.pantry_items,
            request.use_soon_ingredients,
        )
        return RecipeResponse.model_validate({**recipe.model_dump(), **coverage})


async def generate_recipe(
    request: RecipeRequest,
    use_ai: bool = True,
    provider: str = "auto",
) -> RecipeResponse:
    service = RecipeApplicationService()
    return await service.generate_recipe(request, use_ai=use_ai, provider=provider)
