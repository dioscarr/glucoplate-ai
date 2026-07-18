from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_html_pages_receive_native_ingredient_script() -> None:
    response = client.get('/static/index.html')
    assert response.status_code == 200
    assert '<script src="/static/native-ingredients.js" defer></script>' in response.text


def test_native_ingredient_script_exposes_clipboard_camera_and_indexeddb() -> None:
    script = (ROOT / 'app' / 'static' / 'native-ingredients.js').read_text(encoding='utf-8')
    assert 'navigator.clipboard' in script
    assert 'capture="environment"' in script
    assert 'indexedDB.open' in script
    assert 'cacheRecipe' in script
    assert 'cachedRecipes' in script


def test_native_ingredient_script_has_specific_food_iconography() -> None:
    script = (ROOT / 'app' / 'static' / 'native-ingredients.js').read_text(encoding='utf-8')

    assert 'INGREDIENT_ICONS' in script
    assert 'ingredientIconFor' in script
    assert "'🍌'" in script
    assert "'🧅'" in script
    assert "'🧄'" in script
    assert "'🥩'" in script
    assert "'🍤'" in script
    assert "'🍚'" in script
    assert "'🥄'" in script
    assert 'window.ingredientIcon=ingredientIconFor' in script


def test_service_worker_caches_native_ingredient_script() -> None:
    worker = (ROOT / 'app' / 'static' / 'sw.js').read_text(encoding='utf-8')
    assert '/static/native-ingredients.js' in worker
    assert "glucoplate-shell-v7" in worker


def test_recipe_ingredient_icons_open_accessible_zoom_preview() -> None:
    script = (ROOT / 'app' / 'static' / 'native-ingredients.js').read_text(encoding='utf-8')
    assert 'installIngredientZoom' in script
    assert 'openIngredientZoom' in script
    assert 'role="dialog"' in script
    assert "icon.tabIndex=0" in script
    assert "event.key==='Enter'||event.key===' '" in script
    assert "event.key==='Escape'" in script


def test_ingredient_zoom_is_touch_friendly_and_cached() -> None:
    css = (ROOT / 'app' / 'static' / 'ingredient-zoom.css').read_text(encoding='utf-8')
    worker = (ROOT / 'app' / 'static' / 'sw.js').read_text(encoding='utf-8')
    assert 'font-size:clamp(7rem,35vw,11rem)' in css
    assert 'touch-action:manipulation' in css
    assert 'prefers-reduced-motion:reduce' in css
    assert '/static/ingredient-zoom.css' in worker
