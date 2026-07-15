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


def test_service_worker_caches_native_ingredient_script() -> None:
    worker = (ROOT / 'app' / 'static' / 'sw.js').read_text(encoding='utf-8')
    assert '/static/native-ingredients.js' in worker
    assert "glucoplate-shell-v5" in worker
