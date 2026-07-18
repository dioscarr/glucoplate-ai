from pathlib import Path

import pytest

from app.schemas.recipe import NutritionEstimate, RecipeRequest, RecipeResponse, SafetyReview
from app.services.pantry_coverage_service import PantryCoverageService
from app.services.recipe_generator import RecipeApplicationService

ROOT = Path(__file__).resolve().parents[1]


def test_coverage_separates_available_missing_optional_and_use_soon() -> None:
    result = PantryCoverageService().analyze(
        ["2 chicken thighs", "1 cup rice", "cilantro for garnish"],
        pantry_items=["chicken thighs", "onion"],
        use_soon_ingredients=["chicken thighs"],
    )

    assert result["already_have"] == ["2 chicken thighs"]
    assert result["need_to_buy"] == ["1 cup rice"]
    assert result["optional"] == ["cilantro for garnish"]
    assert result["use_soon_matches"] == ["2 chicken thighs"]
    assert result["pantry_coverage"]["coverage_percent"] == 50


class FakeOrchestrator:
    async def generate(self, request, use_ai=True, provider="auto") -> RecipeResponse:
        return RecipeResponse(
            title="Chicken rice bowl",
            summary="A quick dinner.",
            ingredients=["chicken thighs", "rice", "optional lime wedges"],
            steps=["Cook and serve."],
            nutrition_estimate=NutritionEstimate(),
            substitutions=[],
            safety_review=SafetyReview(approved=True, warnings=[], disclaimer="Estimate only."),
            ai_provider="test",
        )


@pytest.mark.asyncio
async def test_application_service_enriches_generated_recipe() -> None:
    request = RecipeRequest(
        goal="dinner",
        pantry_items=["chicken thighs"],
        use_soon_ingredients=["chicken thighs"],
    )
    recipe = await RecipeApplicationService(orchestrator=FakeOrchestrator()).generate_recipe(request)

    assert recipe.already_have == ["chicken thighs"]
    assert recipe.need_to_buy == ["rice"]
    assert recipe.optional == ["optional lime wedges"]
    assert recipe.use_soon_matches == ["chicken thighs"]
    assert recipe.pantry_coverage.coverage_percent == 50


def test_prompt_and_web_client_include_pantry_contracts() -> None:
    orchestrator = (ROOT / "app" / "ai" / "recipe_orchestrator.py").read_text(encoding="utf-8")
    client = (ROOT / "app" / "static" / "pantry-generation.js").read_text(encoding="utf-8")
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")

    assert "Prefer ingredients from pantry" in orchestrator
    assert "use_soon_ingredients" in client
    assert "expiration_status!=='expired'" in client
    assert "pantry_coverage" in client
    assert "need_to_buy" in client
    assert '"/static/pantry-generation.js"' in main
    assert "/static/pantry-generation.js" in worker
    assert "glucoplate-shell-v10" in worker
