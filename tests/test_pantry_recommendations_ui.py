from pathlib import Path

from app.services.recipe_recommendation_service import RecipeRecommendationService

ROOT = Path(__file__).resolve().parents[1]


def test_use_soon_pantry_items_boost_matching_concepts() -> None:
    service = RecipeRecommendationService()
    candidates = [
        {
            "id": "chicken",
            "title": "Quick Chicken Dinner",
            "direction": "A practical chicken meal",
            "tags": ["chicken", "quick"],
        },
        {
            "id": "pasta",
            "title": "Simple Pasta Dinner",
            "direction": "A practical pasta meal",
            "tags": ["pasta", "quick"],
        },
    ]
    pantry = [
        {
            "name": "Chicken thighs",
            "category": "protein",
            "expiration_status": "use_soon",
        }
    ]

    ranked = service.rank(
        "dinner",
        interactions=[],
        candidates=candidates,
        pantry_items=pantry,
        limit=2,
    )

    assert ranked[0]["id"] == "chicken"
    assert ranked[0]["score"] == service.PANTRY_WEIGHT + service.USE_SOON_BONUS
    assert ranked[0]["pantry_matches"] == ["Chicken thighs"]
    assert "before it expires" in ranked[0]["why_this_fits"][0]


def test_pantry_ui_uses_authenticated_profile_scoped_crud() -> None:
    script = (ROOT / "app" / "static" / "pantry-ui.js").read_text(encoding="utf-8")

    assert "/api/pantry/items?profile_id=" in script
    assert "method:'POST'" in script
    assert "method:'DELETE'" in script
    assert "glucoplate_firebase_id_token" in script
    assert "activeProfileId" in script
    assert "use_soon_count" in script
    assert "expired_count" in script


def test_pantry_ui_is_injected_and_cached() -> None:
    main_source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    service_worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")

    assert '"/static/pantry-ui.js"' in main_source
    assert "/static/pantry-ui.js" in service_worker
    assert "const CACHE='glucoplate-shell-v" in service_worker


def test_recommendation_route_loads_pantry_non_blockingly() -> None:
    source = (ROOT / "app" / "api" / "recommendation_routes.py").read_text(encoding="utf-8")

    assert "FirebasePantryService" in source
    assert "pantry_items=pantry_items" in source
    assert "except Exception" in source
    assert 'ranking_version = "flavor-memory-pantry-v1"' in source
    assert '"pantry_count"' in source
    assert '"use_soon_count"' in source
