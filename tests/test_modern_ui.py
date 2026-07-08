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


def test_index_page_has_core_ux_anchors() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "Modern AI meal-planning workspace" in html
    assert "From meal idea to" in html
    assert "Build today’s plate" in html
    assert "Recipe workspace" in html
    assert "Shopping control center" in html


def test_index_page_has_mobile_navigation() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "dock" in html
    assert "Mobile app navigation" in html
    assert "Mobile section shortcuts" in html
    assert "jumpToSection" in html
    assert "composer" in html
    assert "recipe" in html
    assert "products" in html
    assert "stores" in html
    assert "mapSection" in html


def test_index_page_has_ios_style_glass_motion() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "orb" in html
    assert "backdrop-filter:blur" in html
    assert "@keyframes floatOrb" in html
    assert "@keyframes cardLift" in html
    assert "@keyframes shimmer" in html
    assert "@media(prefers-reduced-motion:reduce)" in html


def test_index_page_protects_connected_user_journey() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "/api/recipes/generate" in html
    assert "/api/products/search" in html
    assert "/api/stores/search" in html
    assert "/api/carts" in html
    assert "/api/route/plan" in html
    assert "/api/ai/health" in html


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
