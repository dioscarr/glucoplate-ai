from app.ai.recipe_orchestrator import RecipeOrchestrator
from app.schemas.recipe import RecipeRequest, RecipeResponse


class RecipeApplicationService:
    def __init__(self, orchestrator: RecipeOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or RecipeOrchestrator()

    async def generate_recipe(self, request: RecipeRequest, use_ai: bool = True) -> RecipeResponse:
        return await self.orchestrator.generate(request, use_ai=use_ai)


async def generate_recipe(request: RecipeRequest, use_ai: bool = True) -> RecipeResponse:
    service = RecipeApplicationService()
    return await service.generate_recipe(request, use_ai=use_ai)
