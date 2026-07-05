from app.schemas.recipe import NutritionEstimate, RecipeRequest


class NutritionService:
    """MVP nutrition estimator.

    This is intentionally approximate. Later versions can replace this with USDA
    FoodData Central, OpenFoodFacts, or a local nutrition database.
    """

    def estimate_from_request(self, request: RecipeRequest) -> NutritionEstimate:
        target_carbs = request.max_carbs_per_serving or 45
        return NutritionEstimate(
            calories=450,
            protein_g=32,
            carbs_g=min(target_carbs, 45),
            fiber_g=8,
            sugar_g=6,
            fat_g=18,
            sodium_mg=520,
        )
