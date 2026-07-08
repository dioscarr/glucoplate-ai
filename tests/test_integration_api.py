from __future__ import annotations

import urllib.error
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import cart_store_service, recipe_store_service


client = TestClient(app)


def test_health_endpoint_returns_healthy() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_recipe_generation_uses_local_fallback_when_ai_disabled() -> None:
    response = client.post(
        "/api/recipes/generate?use_ai=false",
        json={
            "goal": "quick Dominican-style dinner",
            "servings": 2,
            "max_carbs_per_serving": 45,
            "preferences": ["high protein", "simple"],
            "avoid_ingredients": ["sugar"],
            "culture": "Dominican",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"]
    assert payload["ingredients"]
    assert payload["steps"]
    assert payload["ai_provider"] == "local-fallback"
    assert payload["safety_review"]["disclaimer"]
    assert payload["nutrition_estimate"]["carbs_g"] is not None


def test_recipe_save_and_list_are_file_backed_but_test_isolated(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(recipe_store_service, "STORE_PATH", str(tmp_path / "recipes.json"))

    response = client.post(
        "/api/recipes/save",
        json={
            "title": "Test Plate",
            "summary": "A test-safe recipe.",
            "ingredients": ["beans", "greens"],
            "steps": ["Cook", "Serve"],
        },
    )

    assert response.status_code == 200
    saved = response.json()["recipe"]
    assert saved["id"].startswith("recipe-")
    assert saved["_saved_at"].endswith("Z")

    list_response = client.get("/api/recipes/list")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "Test Plate"


def test_cart_create_get_update_delete_are_integrated_and_test_isolated(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cart_store_service, "CART_PATH", str(tmp_path / "carts.json"))

    create_response = client.post(
        "/api/carts",
        json={"name": "Weekly groceries", "items": [{"name": "brown rice", "quantity": 1}]},
    )
    assert create_response.status_code == 200
    created = create_response.json()["cart"]
    cart_id = created["id"]

    get_response = client.get(f"/api/carts/{cart_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Weekly groceries"

    update_response = client.put(
        f"/api/carts/{cart_id}",
        json={"name": "Updated groceries", "items": [{"name": "beans", "quantity": 2}]},
    )
    assert update_response.status_code == 200
    assert update_response.json()["ok"] is True
    assert update_response.json()["cart"]["id"] == cart_id
    assert update_response.json()["cart"]["name"] == "Updated groceries"

    delete_response = client.delete(f"/api/carts/{cart_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"ok": True}

    list_response = client.get("/api/carts")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_store_search_falls_back_when_overpass_is_unavailable(monkeypatch) -> None:
    from app.services import store_locator_service

    def fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(store_locator_service.urllib.request, "urlopen", fail_urlopen)

    response = client.post(
        "/api/stores/search",
        json={"latitude": 43.0481, "longitude": -76.1474, "radius_meters": 5000, "query": "grocery"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["source"] == "fallback"
    assert "unavailable" in payload[0]["address"].lower()


def test_product_search_falls_back_when_open_food_facts_is_unavailable(monkeypatch) -> None:
    from app.services import product_lookup_service

    def fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(product_lookup_service.urllib.request, "urlopen", fail_urlopen)

    response = client.post("/api/products/search", json={"ingredient": "brown rice"})

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["ingredient"] == "brown rice"
    assert payload[0]["source"] == "openfoodfacts-unavailable"
    assert payload[0]["availability"] == "unknown"


def test_route_planning_orders_stops_without_requiring_osrm(monkeypatch) -> None:
    from app.services import route_service

    def fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(route_service.urllib.request, "urlopen", fail_urlopen)

    response = client.post(
        "/api/route/plan",
        json={
            "start_lat": 43.0481,
            "start_lng": -76.1474,
            "stops": [
                {"id": "far", "name": "Far Store", "latitude": 43.2, "longitude": -76.3},
                {"id": "near", "name": "Near Store", "latitude": 43.05, "longitude": -76.15},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["order_indexes"][0] == 1
    assert payload["ordered_stops"][0]["id"] == "near"
    assert payload["total_distance_m"] > 0


def test_static_index_is_served() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "GlucoPlate AI" in response.text
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
