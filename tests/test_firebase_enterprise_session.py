from __future__ import annotations

from app.api import firebase_auth_routes


def test_firebase_session_upserts_enterprise_member(monkeypatch) -> None:
    verified_user = {
        "uid": "firebase-user-1",
        "email": "cook@example.com",
        "name": "Cook User",
        "claims": {
            "company_id": "glucoplate",
            "company_name": "GlucoPlate AI",
            "role": "member",
        },
    }
    sync_calls: list[tuple[dict, dict]] = []

    monkeypatch.setattr(
        firebase_auth_routes,
        "_verified_user",
        lambda authorization: {
            **verified_user,
            "claims": dict(verified_user["claims"]),
        },
    )

    def fake_sync(user: dict, claims: dict) -> dict:
        sync_calls.append((dict(user), dict(claims)))
        return {
            "user_id": user["uid"],
            "email": user["email"],
            "display_name": user["name"],
            "role": claims["role"],
            "membership_status": "active",
        }

    monkeypatch.setattr(firebase_auth_routes, "_sync_enterprise_directory", fake_sync)

    payload = firebase_auth_routes.firebase_session("Bearer valid-token")

    assert payload["enterprise"] == {
        "company_id": "glucoplate",
        "company_name": "GlucoPlate AI",
        "role": "member",
    }
    assert payload["membership"]["user_id"] == "firebase-user-1"
    assert sync_calls == [
        (
            {
                "uid": "firebase-user-1",
                "email": "cook@example.com",
                "name": "Cook User",
            },
            {
                "company_id": "glucoplate",
                "company_name": "GlucoPlate AI",
                "role": "member",
            },
        )
    ]


def test_firebase_session_without_enterprise_claims_does_not_sync(monkeypatch) -> None:
    monkeypatch.setattr(
        firebase_auth_routes,
        "_verified_user",
        lambda authorization: {
            "uid": "firebase-user-2",
            "email": "guest@example.com",
            "name": "Guest User",
            "claims": {},
        },
    )

    sync_calls: list[tuple[dict, dict]] = []

    def fake_sync(user: dict, claims: dict) -> dict:
        sync_calls.append((user, claims))
        return {}

    monkeypatch.setattr(firebase_auth_routes, "_sync_enterprise_directory", fake_sync)

    payload = firebase_auth_routes.firebase_session("Bearer valid-token")

    assert payload["enterprise"] is None
    assert payload["membership"] is None
    assert sync_calls == []
