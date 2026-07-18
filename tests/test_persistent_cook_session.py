from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_html_loads_persistent_cooking_session_client() -> None:
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert '<script src="/static/persistent-cook-session.js" defer></script>' in response.text


def test_persistent_client_wraps_progress_completion_and_restore() -> None:
    script = (ROOT / "app" / "static" / "persistent-cook-session.js").read_text(encoding="utf-8")
    assert "/api/user-data/cooking-sessions" in script
    assert "/cooking-sessions/active" in script
    assert "window.startCookMode=wrapped" in script
    assert "window.nextStep=wrapped" in script
    assert "window.prevStep=wrapped" in script
    assert "status:'completed'" in script
    assert "restoreSession" in script
    assert "window.currentRecipe=active.recipe" in script
    assert "window.cookIndex=Math.max" in script


def test_persistent_client_has_offline_cache_and_reconnect_sync() -> None:
    script = (ROOT / "app" / "static" / "persistent-cook-session.js").read_text(encoding="utf-8")
    assert "CACHE_PREFIX" in script
    assert "userId()" in script
    assert "activeProfileId()" in script
    assert "localStorage.setItem(cacheKey()" in script
    assert "syncLocalSession" in script
    assert "window.addEventListener('online'" in script
    assert "GlucoPlateFirebaseAuth?.getIdToken" in script
    assert "response.status===401" in script


def test_service_worker_caches_persistent_session_client() -> None:
    worker = client.get("/static/sw.js")
    assert worker.status_code == 200
    assert "/static/persistent-cook-session.js" in worker.text
    assert "glucoplate-shell-v15" in worker.text
