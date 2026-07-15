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


def clear_firebase_environment(monkeypatch) -> None:
    for name in (
        "FIREBASE_WEB_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_STORAGE_BUCKET",
        "FIREBASE_MESSAGING_SENDER_ID",
        "FIREBASE_APP_ID",
        "FIREBASE_VAPID_PUBLIC_KEY",
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "PUSH_ADMIN_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


def test_push_config_is_safe_when_firebase_is_not_configured(monkeypatch) -> None:
    clear_firebase_environment(monkeypatch)

    response = client.get("/api/push/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported"] is True
    assert payload["provider"] == "firebase"
    assert payload["configured"] is False
    assert payload["client_configured"] is False
    assert payload["server_configured"] is False
    assert payload["vapid_public_key"] == ""
    assert payload["firebase_config"] == {
        "apiKey": "",
        "authDomain": "",
        "projectId": "",
        "storageBucket": "",
        "messagingSenderId": "",
        "appId": "",
    }


def test_firebase_device_token_can_be_saved(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GLUCOPLATE_PUSH_STORE", str(tmp_path / "push_tokens.json"))
    token = "firebase-device-token-abcdefghijklmnopqrstuvwxyz"

    response = client.post(
        "/api/push/tokens",
        json={
            "token": token,
            "user_id": "user-1",
            "profile_id": "profile-1",
            "device_name": "pytest browser",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["subscription"]["token"] == token
    assert payload["subscription"]["provider"] == "firebase"
    assert payload["subscription"]["user_id"] == "user-1"
    assert payload["subscription"]["profile_id"] == "profile-1"


def test_send_endpoint_requires_admin_key(monkeypatch) -> None:
    monkeypatch.setenv("PUSH_ADMIN_KEY", "test-admin-key")

    response = client.post(
        "/api/push/send",
        json={"title": "Dinner ready", "body": "Open your recipe."},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Push administrator key is required"


def test_send_endpoint_reports_unconfigured_with_valid_admin_key(monkeypatch) -> None:
    clear_firebase_environment(monkeypatch)
    monkeypatch.setenv("PUSH_ADMIN_KEY", "test-admin-key")

    response = client.post(
        "/api/push/send",
        headers={"X-Push-Admin-Key": "test-admin-key"},
        json={"title": "Dinner ready", "body": "Open your recipe."},
    )

    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["sent"] == 0
    assert response.json()["failed"] == 0


def test_test_notification_rejects_unregistered_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GLUCOPLATE_PUSH_STORE", str(tmp_path / "push_tokens.json"))
    token = "firebase-device-token-not-registered-abcdefghijklmnop"

    response = client.post(
        "/api/push/test",
        json={"token": token},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "This device is not registered for notifications"
