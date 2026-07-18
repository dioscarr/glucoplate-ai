from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_price_observation_contracts() -> None:
    service = (ROOT / "app" / "services" / "firebase_price_observation_service.py").read_text(encoding="utf-8")
    routes = (ROOT / "app" / "api" / "price_observation_routes.py").read_text(encoding="utf-8")
    comparison = (ROOT / "app" / "services" / "shopping_comparison_service.py").read_text(encoding="utf-8")
    ui = (ROOT / "app" / "static" / "shopping-list-ui.js").read_text(encoding="utf-8")
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")

    assert "price_observations" in service
    assert "MAX_AGE_DAYS = 90" in service
    assert '"reported": False' in service
    assert "reporter_hash" in service
    assert "minimum_price" in service
    assert "maximum_price" in service
    assert "confidence" in service
    assert '@router.post("")' in routes
    assert '@router.get("/summary")' in routes
    assert '@router.post("/{observation_id}/report")' in routes
    assert "user-submitted" in routes
    assert "receipt-extracted" in routes
    assert "retailer-supplied" in routes
    assert "community_price" in comparison
    assert "effective_price" in comparison
    assert "Submit price" in ui
    assert "/api/price-observations" in ui
    assert "price_observation_router" in main
    assert 'version="0.14.0"' in main
    assert "glucoplate-shell-v13" in worker
