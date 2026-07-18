from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_html_receives_recommendation_ui_script() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert '<script src="/static/recommendation-ui.js" defer></script>' in response.text


def test_recommendation_ui_wraps_generation_and_preserves_fallback() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")

    assert "/api/recommendations/recipe-concepts" in script
    assert "window.generateRecipe=recommendBeforeGenerate" in script
    assert "originalGenerate" in script
    assert "why_this_fits" in script
    assert "profile_id:activeProfileId()" in script


def test_service_worker_caches_recommendation_ui() -> None:
    response = client.get("/static/sw.js")

    assert response.status_code == 200
    assert "/static/recommendation-ui.js" in response.text
    assert "glucoplate-shell-v8" in response.text
