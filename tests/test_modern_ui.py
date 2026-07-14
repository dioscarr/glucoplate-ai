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
    assert "% match" in html
    assert "scoreIdea" in html


def test_index_page_has_milestone_2_native_app_shell() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "Home" in html
    assert "Discover" in html
    assert "Cookbook" in html
    assert "Profile" in html
    assert "Mobile app navigation" in html
    assert "categoryRow" in html
    assert "AI kitchen" in html
    assert "thinking" in html
    assert "Cook Mode" in html
    assert "startCookMode" in html


def test_index_page_has_polished_cook_mode() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "cook-progress" in html
    assert "Kitchen timer" in html
    assert "toggleTimer" in html
    assert "timerSeconds" in html
    assert "Recipe complete" in html
    assert "prevCookStep" in html
    assert "nextCookStep" in html


def test_index_page_has_motion_system_tokens() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "--fast" in html
    assert "--medium" in html
    assert "--slow" in html
    assert "--spring" in html
    assert "@keyframes fadeLift" in html
    assert "@keyframes chipPop" in html
    assert "@keyframes heroFloat" in html
    assert "@keyframes toastIn" in html
    assert "@media(prefers-reduced-motion:reduce)" in html


def test_index_page_has_sticky_recipe_actions_and_saved_cards() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "position:sticky" in html
    assert "recipe-actions" in html
    assert "saved-emoji" in html
    assert "Saved recipe" in html
    assert "New recipe" in html


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
