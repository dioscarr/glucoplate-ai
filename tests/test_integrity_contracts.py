from __future__ import annotations

from pathlib import Path

from app.ai.recipe_orchestrator import RecipeOrchestrator
from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.schemas.store import ProductAvailability, ProductSearchRequest, Store, StoreSearchRequest
from app.services.fallback_recipe_service import FallbackRecipeService


ROOT = Path(__file__).resolve().parents[1]


def test_recipe_request_contract_accepts_expected_fields() -> None:
    request = RecipeRequest(
        goal="quick dinner",
        servings=2,
        max_carbs_per_serving=45,
        preferences=["high fiber"],
        avoid_ingredients=["sugar"],
        culture="Dominican",
    )

    assert request.goal == "quick dinner"
    assert request.servings == 2
    assert request.max_carbs_per_serving == 45
    assert request.preferences == ["high fiber"]
    assert request.avoid_ingredients == ["sugar"]
    assert request.culture == "Dominican"


def test_fallback_recipe_response_matches_public_contract() -> None:
    response = FallbackRecipeService().generate(
        RecipeRequest(goal="balanced lunch", servings=1, max_carbs_per_serving=35)
    )

    payload = response.model_dump()
    assert set(payload) == {
        "title",
        "summary",
        "ingredients",
        "steps",
        "nutrition_estimate",
        "substitutions",
        "safety_review",
        "ai_provider",
    }
    assert RecipeResponse.model_validate(payload)
    assert payload["ai_provider"] == "local-fallback"
    assert payload["safety_review"]["approved"] in {True, False}
    assert payload["safety_review"]["disclaimer"]


def test_store_and_product_contracts_preserve_source_and_uncertainty() -> None:
    store_request = StoreSearchRequest(latitude=43.0481, longitude=-76.1474)
    store = Store(
        id="1",
        name="Test Store",
        latitude=store_request.latitude,
        longitude=store_request.longitude,
    )
    product_request = ProductSearchRequest(ingredient="beans")
    product = ProductAvailability(ingredient=product_request.ingredient, source="openfoodfacts")

    assert store.source == "openstreetmap"
    assert product.source == "openfoodfacts"
    assert product.availability == "unknown"
    assert product.price is None
    assert product.currency is None


def test_recipe_orchestrator_exposes_expected_agent_chain() -> None:
    orchestrator = RecipeOrchestrator()

    assert orchestrator.planner_agent is not None
    assert orchestrator.recipe_agent is not None
    assert orchestrator.nutrition_agent is not None
    assert orchestrator.safety_agent is not None
    assert orchestrator.reviewer_agent is not None
    assert orchestrator.fallback_service is not None


def test_static_ui_does_not_reintroduce_browser_dialogs() -> None:
    index_html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")

    banned_dialog_calls = ["alert(", "confirm(", "prompt("]
    for banned_call in banned_dialog_calls:
        assert banned_call not in index_html, f"Replace {banned_call} with toast or mini-modal UX."


def test_static_ui_keeps_modal_and_toast_language_available() -> None:
    index_html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8").lower()

    assert "modal" in index_html
    assert "toast" in index_html


def test_documentation_booklet_exists_for_architecture_context() -> None:
    booklet = ROOT / "docs" / "DESIGN_AND_ENGINEERING_BOOKLET.md"

    assert booklet.exists()
    text = booklet.read_text(encoding="utf-8")
    assert "High-Level System Design" in text
    assert "Twenty Product Use Cases" in text
    assert "Architectural Design" in text
