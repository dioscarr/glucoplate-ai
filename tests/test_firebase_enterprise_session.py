from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import enterprise_admin_routes, firebase_auth_routes
from app.main import app


client = TestClient(app)


class FakeDirectory:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def upsert_authenticated_user(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {
            "user_id": kwargs["firebase_uid"],
            "email": kwargs["email"],
            "display_name": kwargs["display_name"],
            "role": kwargs["role"],
            "membership_status": "active",
        }


def test_firebase_session_upserts_enterprise_member(monkeypatch) -> None:
    fake_directory = FakeDirectory()
    monkeypatch.setattr(
        firebase_auth_routes.FirebaseAuthService,
        "verify_id_token",
        lambda self, token: {
            "uid": "firebase-user-1",
            "email": "cook@example.com",
            "name": "Cook User",
            "claims": {
                "company_id": "glucoplate",
                "company_name": "GlucoPlate AI",
                "role": "member",
            },
        },
    )
    monkeypatch.setattr(enterprise_admin_routes, "directory", lambda: fake_directory)

    response = client.get(
        "/api/firebase-auth/session",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["enterprise"]["company_id"] == "glucoplate"
    assert payload["membership"]["user_id"] == "firebase-user-1"
    assert fake_directory.calls == [
        {
            "firebase_uid": "firebase-user-1",
            "email": "cook@example.com",
            "display_name": "Cook User",
            "enterprise_id": "glucoplate",
            "role": "member",
        }
    ]


def test_firebase_session_without_enterprise_claims_does_not_sync(monkeypatch) -> None:
    fake_directory = FakeDirectory()
    monkeypatch.setattr(
        firebase_auth_routes.FirebaseAuthService,
        "verify_id_token",
        lambda self, token: {
            "uid": "firebase-user-2",
            "email": "guest@example.com",
            "name": "Guest User",
            "claims": {},
        },
    )
    monkeypatch.setattr(enterprise_admin_routes, "directory", lambda: fake_directory)

    response = client.get(
        "/api/firebase-auth/session",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["enterprise"] is None
    assert payload["membership"] is None
    assert fake_directory.calls == []
