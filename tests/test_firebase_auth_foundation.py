from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_firebase_auth_config_is_safe_when_unconfigured(monkeypatch) -> None:
    for name in (
        "FIREBASE_WEB_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_APP_ID",
        "FIREBASE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        monkeypatch.delenv(name, raising=False)

    response = client.get("/api/firebase-auth/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "firebase"
    assert payload["client_configured"] is False
    assert payload["server_configured"] is False
    assert "serviceAccount" not in str(payload)


def test_firebase_session_requires_bearer_token() -> None:
    response = client.get("/api/firebase-auth/session")
    assert response.status_code == 401
    assert "bearer token" in response.json()["detail"].lower()


def test_html_pages_receive_firebase_auth_client() -> None:
    for path in ("/static/index.html", "/static/login.html", "/static/register.html"):
        response = client.get(path)
        assert response.status_code == 200
        assert '<script src="/static/firebase-auth.js" defer></script>' in response.text


def test_firebase_auth_client_supports_google_and_signout() -> None:
    script = (ROOT / "app" / "static" / "firebase-auth.js").read_text(encoding="utf-8")
    assert "GoogleAuthProvider" in script
    assert "signInWithPopup" in script
    assert "onAuthStateChanged" in script
    assert "signOut" in script
    assert "/api/firebase-auth/enterprise/enroll" in script
    assert "/api/firebase-auth/session" in script
    assert "Authorization:`Bearer ${token}`" in script


def test_service_worker_caches_firebase_auth_client() -> None:
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert "/static/firebase-auth.js" in worker
