from pathlib import Path

from fastapi.testclient import TestClient

from app.api.enterprise_admin_routes import AuthContext, current_user
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


def test_push_config_is_safe_when_firebase_is_not_configured(monkeypatch) -> None:
    for name in (
        "FIREBASE_WEB_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_APP_ID",
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "VAPID_PUBLIC_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    response = client.get("/api/push/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["supported"] is True
    assert payload["provider"] == "firebase"
    assert payload["configured"] is False
    assert payload["client_configured"] is False
    assert payload["server_configured"] is False
    assert payload["vapid_public_key"] == ""
    assert "serviceAccount" not in str(payload)


def test_push_token_can_be_saved(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GLUCOPLATE_PUSH_STORE", str(tmp_path / "push.json"))
    token = "test-device-token-1234567890"
    app.dependency_overrides[current_user] = lambda: AuthContext(
        uid="user-1", enterprise_id="glucoplate", role="member"
    )
    response = client.post(
        "/api/push/tokens",
        json={
            "token": token,
            "user_id": "user-1",
            "profile_id": "profile-1",
            "device_name": "pytest device",
        },
    )
    try:
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["subscription"]["token"] == token
        assert payload["subscription"]["user_id"] == "user-1"
        assert payload["subscription"]["enterprise_id"] == "glucoplate"
    finally:
        app.dependency_overrides.clear()


def test_send_endpoint_requires_admin_key(monkeypatch) -> None:
    monkeypatch.delenv("PUSH_ADMIN_KEY", raising=False)
    response = client.post(
        "/api/push/send",
        json={"title": "Dinner ready", "body": "Open your recipe."},
    )
    assert response.status_code == 403
    assert "administrator key" in response.json()["detail"].lower()
