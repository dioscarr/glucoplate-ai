from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_manifest_is_served_as_pwa_manifest() -> None:
    response = client.get("/static/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    payload = response.json()
    assert payload["display"] == "standalone"
    assert payload["id"] == "/static/index.html"
    assert payload["icons"]


def test_service_worker_has_root_scope_header() -> None:
    response = client.get("/static/sw.js")
    assert response.status_code == 200
    assert response.headers["service-worker-allowed"] == "/"
    assert "notificationclick" in response.text
    assert "showNotification" in response.text


def test_html_pages_receive_pwa_client_script() -> None:
    for path in ("/static/index.html", "/static/login.html", "/static/register.html"):
        response = client.get(path)
        assert response.status_code == 200
        assert '<script src="/static/pwa.js" defer></script>' in response.text


def test_pwa_client_exposes_ios_native_capabilities() -> None:
    script = client.get("/static/pwa.js")
    assert script.status_code == 200
    text = script.text
    assert "safe-area-inset-top" in text
    assert "safe-area-inset-bottom" in text
    assert "navigator.share" in text
    assert "navigator.wakeLock" in text
    assert "startViewTransition" in text
    assert "visualViewport" in text
    assert "showInstallSheet" in text
    assert "touchstart" in text
    assert "Add to Home Screen" in text


def test_pwa_panel_is_rendered_on_home_with_native_actions() -> None:
    text = client.get("/static/pwa.js").text
    assert "homeView" in text
    assert "Share" in text
    assert "Keep screen awake" in text
    assert "Enable notifications" in text
    assert "Install app" in text


def test_push_config_is_safe_when_vapid_is_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    response = client.get("/api/push/config")
    assert response.status_code == 200
    assert response.json() == {
        "supported": True,
        "configured": False,
        "vapid_public_key": "",
    }


def test_push_subscription_can_be_saved(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GLUCOPLATE_PUSH_STORE", str(tmp_path / "push.json"))
    response = client.post(
        "/api/push/subscriptions",
        json={
            "subscription": {
                "endpoint": "https://push.example.test/device-1",
                "keys": {"p256dh": "test-key", "auth": "test-auth"},
            },
            "user_id": "user-1",
            "profile_id": "profile-1",
        },
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_send_endpoint_reports_unconfigured_without_exposing_secrets(monkeypatch) -> None:
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    response = client.post(
        "/api/push/send",
        json={"title": "Dinner ready", "body": "Open your recipe."},
    )
    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["sent"] == 0
