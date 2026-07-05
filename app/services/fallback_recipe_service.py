from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.nutrition_service import NutritionService
from app.services.safety_service import SafetyService


class FallbackRecipeService:
    def __init__(
        self,
        recipe_repository: RecipeRepository | None = None,
        nutrition_service: NutritionService | None = None,
        safety_service: SafetyService | None = None,
    ) -> None:
        self.recipe_repository = recipe_repository or RecipeRepository()
        self.nutrition_service = nutrition_service or NutritionService()
        self.safety_service = safety_service or SafetyService()

    def generate(self, request: RecipeRequest) -> RecipeResponse:
        matches = self.recipe_repository.search_by_culture_or_goal(request.culture, request.goal)
        base = matches[0] if matches else {}
        title = base.get("title") or f"Balanced {request.goal.title()}"
        ingredients = base.get("ingredients") or [
            "lean protein",
            "non-starchy vegetables",
            "high-fiber carbohydrate portion",
            "healthy fat",
            "herbs and spices",
        ]

        summary = base.get("notes") or (
            "A balanced diabetes-conscious meal idea with protein, fiber, vegetables, "
            "and controlled carbohydrate portions."
        )

        steps = [
            "Prepare the lean protein using grilling, baking, or sauteing.",
            "Cook or warm vegetables with herbs and a small amount of healthy fat.",
            "Add a controlled portion of high-fiber carbohydrates if desired.",
            "Plate with vegetables first, then protein, then carbohydrate portion.",
            "Taste and adjust with citrus, herbs, or salt-free seasoning."
        ]

        safety_review = self.safety_service.review_text(" ".join([title, summary, *ingredients, *steps]))

        return RecipeResponse(
            title=title,
            summary=summary,
            ingredients=ingredients,
            steps=steps,
            nutrition_estimate=self.nutrition_service.estimate_from_request(request),
            substitutions=[
                "Swap white rice for cauliflower rice or a smaller portion of brown rice.",
                "Use skinless chicken, fish, tofu, or beans for protein variety.",
                "Add extra non-starchy vegetables to increase volume and fiber."
            ],
            safety_review=safety_review,
            ai_provider="local-fallback",
        )
