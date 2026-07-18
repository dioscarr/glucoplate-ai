from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.firebase_pantry_service import FirebasePantryService

ROOT = Path(__file__).resolve().parents[1]


def test_expiration_status_marks_expired_use_soon_and_fresh() -> None:
    today = datetime.now(UTC).date()

    expired = FirebasePantryService._with_expiration_status(
        {"name": "Spinach", "expiration_date": (today - timedelta(days=1)).isoformat()}
    )
    use_soon = FirebasePantryService._with_expiration_status(
        {"name": "Chicken", "expiration_date": (today + timedelta(days=2)).isoformat()}
    )
    fresh = FirebasePantryService._with_expiration_status(
        {"name": "Rice", "expiration_date": (today + timedelta(days=30)).isoformat()}
    )

    assert expired["expiration_status"] == "expired"
    assert expired["days_until_expiration"] == -1
    assert use_soon["expiration_status"] == "use_soon"
    assert use_soon["days_until_expiration"] == 2
    assert fresh["expiration_status"] == "fresh"


def test_missing_or_invalid_expiration_is_unknown() -> None:
    missing = FirebasePantryService._with_expiration_status({"name": "Salt"})
    invalid = FirebasePantryService._with_expiration_status(
        {"name": "Milk", "expiration_date": "tomorrow"}
    )

    assert missing["expiration_status"] == "unknown"
    assert missing["days_until_expiration"] is None
    assert invalid["expiration_status"] == "unknown"


def test_pantry_routes_are_profile_scoped_and_authenticated() -> None:
    routes = (ROOT / "app" / "api" / "pantry_routes.py").read_text(encoding="utf-8")
    service = (ROOT / "app" / "services" / "firebase_pantry_service.py").read_text(encoding="utf-8")

    assert 'router = APIRouter(prefix="/api/pantry"' in routes
    assert '@router.post("/items", status_code=201)' in routes
    assert '@router.get("/items")' in routes
    assert '@router.put("/items/{item_id}")' in routes
    assert '@router.delete("/items/{item_id}")' in routes
    assert "Depends(scoped_user)" in routes
    assert "profiles/" in service
    assert "pantry_items" in service
    assert '"profile_id": selected_profile_id' in service


def test_main_registers_pantry_router_and_api_tracking() -> None:
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

    assert "from app.api.pantry_routes import router as pantry_router" in main
    assert "app.include_router(pantry_router)" in main
    assert '"/api/pantry"' in main
