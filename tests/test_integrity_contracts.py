from __future__ import annotations

from pathlib import Path

from app.ai.recipe_orchestrator import RecipeOrchestrator
from app.core.secrets import get_secret
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
        "already_have",
        "need_to_buy",
        "optional",
        "use_soon_matches",
        "pantry_coverage",
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


def test_recipe_orchestrator_exposes_local_fallback() -> None:
    orchestrator = RecipeOrchestrator()

    assert orchestrator.fallback_service is not None
    assert not hasattr(orchestrator, "planner_agent")


def test_secret_provider_reads_first_available_secret_name(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")

    assert get_secret("GEMINI_API_KEY", "GOOGLE_API_KEY") == "test-google-key"


def test_secret_provider_returns_none_when_secret_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("MISSING_SECRET_A", raising=False)
    monkeypatch.delenv("MISSING_SECRET_B", raising=False)

    assert get_secret("MISSING_SECRET_A", "MISSING_SECRET_B") is None


def test_static_ui_does_not_reintroduce_browser_dialogs() -> None:
    index_html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")

    banned_dialog_calls = ["alert(", "confirm(", "prompt("]
    for banned_call in banned_dialog_calls:
        assert banned_call not in index_html, f"Replace {banned_call} with toast or inline UX."


def test_static_ui_keeps_nonblocking_feedback_available() -> None:
    index_html = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8").lower()

    assert "toast" in index_html
    assert "thinking" in index_html


def test_documentation_booklet_exists_for_architecture_context() -> None:
    booklet = ROOT / "docs" / "DESIGN_AND_ENGINEERING_BOOKLET.md"

    assert booklet.exists()
    text = booklet.read_text(encoding="utf-8")
    assert "High-Level System Design" in text
    assert "Twenty Product Use Cases" in text
    assert "Architectural Design" in text


def test_deployment_secrets_document_covers_runtime_and_ci_secrets() -> None:
    doc = ROOT / "docs" / "DEPLOYMENT_SECRETS.md"

    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "Deployment Secrets Strategy" in text
    assert "CI_NOTIFICATION_WEBHOOK_URL" in text
    assert "GEMINI_API_KEY" in text

def test_firebase_auth_emulator_is_explicitly_opt_in() -> None:
    service = __import__("app.services.firebase_auth_service", fromlist=["FirebaseAuthService"]).FirebaseAuthService()
    config = service.client_config

    assert "authEmulatorUrl" in config
    auth_client = (ROOT / "app" / "static" / "firebase-auth.js").read_text(encoding="utf-8")
    assert "connectAuthEmulator" in auth_client
    assert "settings.auth_emulator_url" in auth_client
