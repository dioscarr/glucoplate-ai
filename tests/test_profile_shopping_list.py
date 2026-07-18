from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shopping_list_api_is_profile_scoped() -> None:
    routes = (ROOT / "app" / "api" / "shopping_list_routes.py").read_text(encoding="utf-8")
    service = (ROOT / "app" / "services" / "firebase_shopping_list_service.py").read_text(encoding="utf-8")

    assert 'APIRouter(prefix="/api/shopping-list"' in routes
    assert '@router.post("/items"' in routes
    assert '@router.get("/items")' in routes
    assert '@router.put("/items/{item_id}")' in routes
    assert '@router.delete("/items/{item_id}")' in routes
    assert '@router.delete("/checked")' in routes
    assert "profiles/{selected}/shopping_list_items" in service
    assert "existing_names" in service
    assert '"checked": False' in service


def test_generated_shopping_gap_has_one_tap_persistence() -> None:
    generation = (ROOT / "app" / "static" / "pantry-generation.js").read_text(encoding="utf-8")
    shopping = (ROOT / "app" / "static" / "shopping-list-ui.js").read_text(encoding="utf-8")

    assert "addShoppingGapBtn" in generation
    assert "GlucoPlateShoppingList?.addItems" in generation
    assert "/api/shopping-list/items" in shopping
    assert "source_recipe" in shopping
    assert "Clear checked" in shopping
    assert "data-check-id" in shopping


def test_shopping_list_client_is_injected_and_cached() -> None:
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")

    assert 'version="0.12.0"' in main
    assert '"/static/shopping-list-ui.js"' in main
    assert "shopping_list_router" in main
    assert '"/api/shopping-list"' in main
    assert "/static/shopping-list-ui.js" in worker
    assert "glucoplate-shell-v11" in worker
