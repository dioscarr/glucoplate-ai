from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "app" / "static" / "index.html"
client = TestClient(app)


def test_root_redirects_to_single_index_page() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/static/index.html"


def test_index_page_has_cuisine_first_recipe_discovery() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "Cuisine-first recipe discovery" in html
    assert "Choose a cuisine. Pick a dish. Generate it." in html
    assert "Explore cuisines" in html
    assert "cuisineGrid" in html
    assert "renderPopularRecipes" in html


def test_index_page_has_ingredient_and_food_browsing() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "foodGrid" in html
    assert "selectedFoods" in html
    assert "renderCategories" in html
    assert "renderFoods" in html
    assert "ingredients you already have" in html


def test_index_page_has_native_app_shell() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "homeView" in html
    assert "discoverView" in html
    assert "cookView" in html
    assert "savedView" in html
    assert "profileView" in html
    assert "bottom-nav" in html
    assert "Open Cook Mode" in html


def test_index_page_has_cook_mode() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "cook-step" in html
    assert "cook-controls" in html
    assert "startCookMode" in html
    assert "nextStep" in html


def test_index_page_has_motion_and_feedback() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "@keyframes fadeLift" in html
    assert "@keyframes bounce" in html
    assert "thinking" in html
    assert "toast" in html


def test_index_page_has_sticky_recipe_actions_and_saved_cards() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "position:sticky" in html
    assert "recipe-actions" in html
    assert "saved-list" in html
    assert "saved-item" in html
    assert "loadSaved" in html


def test_index_page_keeps_existing_recipe_journey() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "/api/recipes/generate" in html
    assert "/api/recipes/save" in html
    assert "/api/recipes/list" in html
    assert "renderRecipe" in html
    assert "saveRecipe" in html


def test_index_page_uses_toast_not_browser_dialogs() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "function toast" in html
    assert "alert(" not in html
    assert "confirm(" not in html
    assert "prompt(" not in html


def test_index_page_is_served_with_no_cache_headers() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "GlucoPlate AI" in response.text
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"


def test_duplicate_modern_entry_page_does_not_exist() -> None:
    assert not (ROOT / "app" / "static" / "modern.html").exists()
