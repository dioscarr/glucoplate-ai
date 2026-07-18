from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_access_code_lookup_returns_admin_company() -> None:
    response = client.post("/api/auth/access-code", json={"access_code": "0001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["company"]["company_name"] == "GlucoPlate Admin"
    assert payload["company"]["user_type"] == "AD"


def test_register_creates_user_and_admin_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GLUCOPLATE_AUTH_STORE", str(tmp_path / "auth_store.json"))

    response = client.post(
        "/api/auth/register",
        json={"access_code": "0001", "email": "Admin@Example.com", "name": "Admin User"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "created_user"
    assert payload["user"]["email"] == "admin@example.com"
    assert payload["active_profile"]["user_type"] == "AD"
    assert payload["active_profile"]["company_id"] == "admin"
    assert payload["token"].startswith("demo.")


def test_existing_user_gets_new_profile_for_new_access_code(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GLUCOPLATE_AUTH_STORE", str(tmp_path / "auth_store.json"))

    first = client.post(
        "/api/auth/register",
        json={"access_code": "2001", "email": "cook@example.com", "name": "Cook User"},
    )
    second = client.post(
        "/api/auth/register",
        json={"access_code": "1001", "email": "cook@example.com", "name": "Cook User"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()
    assert payload["status"] == "added_profile"
    assert len(payload["profiles"]) == 2
    assert {profile["user_type"] for profile in payload["profiles"]} == {"ST", "OF"}


def test_login_returns_existing_profiles(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GLUCOPLATE_AUTH_STORE", str(tmp_path / "auth_store.json"))
    client.post(
        "/api/auth/register",
        json={"access_code": "2001", "email": "cook@example.com", "name": "Cook User"},
    )

    response = client.post("/api/auth/login", json={"email": "cook@example.com"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "logged_in"
    assert payload["user"]["email"] == "cook@example.com"
    assert len(payload["profiles"]) == 1


def test_unknown_access_code_and_missing_login_return_404(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GLUCOPLATE_AUTH_STORE", str(tmp_path / "auth_store.json"))

    invalid_code = client.post(
        "/api/auth/register",
        json={"access_code": "9999", "email": "missing@example.com", "name": "Missing"},
    )
    missing_login = client.post("/api/auth/login", json={"email": "missing@example.com"})

    assert invalid_code.status_code == 404
    assert missing_login.status_code == 404


def test_static_auth_pages_are_served_with_no_cache_headers() -> None:
    login = client.get("/static/login.html")
    register = client.get("/static/register.html")

    assert login.status_code == 200
    assert register.status_code == 200
    assert "Welcome back" in login.text
    assert "Access-code registration" in register.text
    assert "No username, password, or access code is needed." in login.text
    assert "Future sign-ins use Google only." in register.text
    assert login.headers["cache-control"] == "no-cache, no-store, must-revalidate"
    assert register.headers["cache-control"] == "no-cache, no-store, must-revalidate"


def test_firebase_gate_uses_google_only_and_access_code_only_for_registration() -> None:
    source = (Path(__file__).resolve().parents[1] / "app" / "static" / "firebase-auth.js").read_text(encoding="utf-8")
    assert "Continue with Google" in source
    assert "Register with Google" in source
    assert "enterpriseAccessCodeField" in source
    assert "codeField.style.display=registering?'grid':'none'" in source
    assert "codeInput.required=registering" in source
    assert "signInWithEmailAndPassword" not in source
    assert "createUserWithEmailAndPassword" not in source
    assert "enterpriseEmail" not in source
    assert "enterprisePassword" not in source
