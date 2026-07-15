from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_html_receives_native_cook_script() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert '<script src="/static/device-manager.js" defer></script>' in response.text
    assert '<script src="/static/native-cook.js" defer></script>' in response.text


def test_native_cook_asset_contains_expected_integrations() -> None:
    script = (ROOT / "app" / "static" / "native-cook.js").read_text(encoding="utf-8")

    assert "requestWakeLock" in script
    assert "shareCurrentRecipe" in script
    assert "touchstart" in script
    assert "touchend" in script
    assert "releaseWakeLock" in script


def test_service_worker_caches_native_cook_asset() -> None:
    response = client.get("/static/sw.js")

    assert response.status_code == 200
    assert "/static/native-cook.js" in response.text
