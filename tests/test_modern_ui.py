from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_root_redirects_to_modern_product_shell() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/static/modern.html"


def test_modern_product_shell_has_core_ux_anchors() -> None:
    html = (ROOT / "app" / "static" / "modern.html").read_text(encoding="utf-8")

    assert "Modern AI meal-planning workspace" in html
    assert "From meal idea to" in html
    assert "Build today’s plate" in html
    assert "Recipe workspace" in html
    assert "Shopping control center" in html
    assert "Classic UI" in html


def test_modern_product_shell_protects_connected_user_journey() -> None:
    html = (ROOT / "app" / "static" / "modern.html").read_text(encoding="utf-8")

    assert "/api/recipes/generate" in html
    assert "/api/products/search" in html
    assert "/api/stores/search" in html
    assert "/api/carts" in html
    assert "/api/route/plan" in html
    assert "/api/ai/health" in html


def test_modern_product_shell_uses_toast_not_browser_dialogs() -> None:
    html = (ROOT / "app" / "static" / "modern.html").read_text(encoding="utf-8")

    assert "function toast" in html
    assert "alert(" not in html
    assert "confirm(" not in html
    assert "prompt(" not in html


def test_modern_product_shell_is_served_with_no_cache_headers() -> None:
    response = client.get("/static/modern.html")

    assert response.status_code == 200
    assert "GlucoPlate AI" in response.text
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate"
