from pathlib import Path

from app.schemas.store import ProductAvailability
from app.services.shopping_comparison_service import ShoppingComparisonService

ROOT = Path(__file__).resolve().parents[1]


class FakeObservationService:
    def aggregate(self, enterprise_id, **kwargs):
        return {}


class FakePriceService:
    def search(self, request):
        price = 3.5 if request.ingredient == "rice" else None
        return [ProductAvailability(
            ingredient=request.ingredient,
            product_name=f"Matched {request.ingredient}",
            price=price,
            currency="$" if price is not None else None,
            availability="unknown",
            source="test-source",
            notes=["Test data"],
        )]


def test_comparison_reports_known_and_unavailable_prices() -> None:
    result = ShoppingComparisonService(FakePriceService(), FakeObservationService()).compare([
        {"id": "1", "name": "rice", "checked": False},
        {"id": "2", "name": "cilantro", "checked": False},
        {"id": "3", "name": "done", "checked": True},
    ], enterprise_id="test-enterprise")

    assert result["item_count"] == 2
    assert result["known_price_count"] == 1
    assert result["known_total"] == 3.5
    assert result["estimate_complete"] is False
    assert result["items"][1]["price_status"] == "unavailable"
    assert "Confirm price and availability" in result["disclaimer"]


def test_route_and_ui_expose_comparison_contract() -> None:
    routes = (ROOT / "app" / "api" / "shopping_list_routes.py").read_text(encoding="utf-8")
    ui = (ROOT / "app" / "static" / "shopping-list-ui.js").read_text(encoding="utf-8")
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

    assert '@router.post("/compare")' in routes
    assert "ShoppingComparisonService" in routes
    assert "/api/shopping-list/compare" in ui
    assert "Price unavailable" in ui
    assert "result.disclaimer" in ui
    assert "const CACHE='glucoplate-shell-v" in worker
