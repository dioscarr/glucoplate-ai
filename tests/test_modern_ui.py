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


def test_index_page_has_food_based_recipe_planner() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "Food-based recipe planner" in html
    assert "Pick food. Get recipe names." in html
    assert "Browse by food" in html
    assert "Browse by image" in html
    assert "Suggest recipe names" in html
    assert "foodGrid" in html
    assert "suggestions" in html


def test_index_page_has_recipe_name_suggestion_flow() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "recipeIdeas" in html
    assert "suggestRecipeNames" in html
    assert "chooseRecipeIdea" in html
    assert "collectFoods" in html
    assert "imageFoodHints" in html
    assert "Make ${idea.name}" in html


def test_index_page_keeps_existing_recipe_journey() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "/api/recipes/generate" in html
    assert "/api/recipes/save" in html
    assert "/api/recipes/list" in html
    assert "renderRecipe" in html
    assert "saveRecipe" in html
    assert "Saved recipes" in html


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
