from __future__ import annotations

import os

import httpx
import pytest


pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def api_client():
    url = os.getenv("LIVE_SITE_URL", "").strip().rstrip("/")
    if not url:
        pytest.skip("LIVE_SITE_URL is only set by the post-deployment workflow")
    timeout = httpx.Timeout(30.0, connect=30.0)
    with httpx.Client(base_url=url, timeout=timeout, follow_redirects=True) as client:
        yield client


def test_container_api_health(api_client: httpx.Client) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "product": "GlucoPlate AI",
    }


def test_production_app_shell_is_served(api_client: httpx.Client) -> None:
    response = api_client.get("/")

    assert response.status_code == 200
    assert "GlucoPlate AI" in response.text
    assert "/static/live-cook-rooms.js" in response.text


def test_production_pwa_assets_are_available(api_client: httpx.Client) -> None:
    manifest = api_client.get("/static/manifest.webmanifest")
    worker = api_client.get("/static/sw.js")

    assert manifest.status_code == 200
    assert "application/manifest+json" in manifest.headers.get("content-type", "")
    assert worker.status_code == 200
    assert "no-cache" in worker.headers.get("cache-control", "")
