from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.enterprise_admin_routes import AuthContext, current_user
from app.api import push_routes
from app.main import app

client = TestClient(app)


class FakePushService:
    records: dict[str, str] = {}

    @property
    def firebase_config(self) -> dict[str, str]:
        return {}

    @property
    def vapid_public_key(self) -> str:
        return ""

    def configured(self) -> bool:
        return False

    def client_configured(self) -> bool:
        return False

    def server_configured(self) -> bool:
        return True

    def save_token(self, token: str, user_id: str | None = None, **kwargs) -> dict:
        self.records[token] = str(user_id)
        return {"token": token, "user_id": user_id, **kwargs}

    def remove_token(self, token: str, user_id: str | None = None, enterprise_id: str | None = None) -> bool:
        if self.records.get(token) != user_id:
            return False
        del self.records[token]
        return True

    def send_to_registered_token(
        self,
        token: str,
        payload: dict,
        user_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> dict:
        registered = self.records.get(token) == user_id
        return {"configured": True, "registered": registered, "sent": int(registered), "failed": 0}


def _as_user(uid: str) -> AuthContext:
    return AuthContext(uid=uid, email=f"{uid}@example.com", enterprise_id="glucoplate")


def test_token_registration_uses_authenticated_uid_not_request_body(monkeypatch) -> None:
    FakePushService.records = {}
    monkeypatch.setattr(push_routes, "PushNotificationService", FakePushService)
    app.dependency_overrides[current_user] = lambda: _as_user("firebase-user-a")
    try:
        response = client.post(
            "/api/push/tokens",
            json={
                "token": "token-value-long-enough-12345",
                "user_id": "attacker-controlled-user",
                "device_name": "test browser",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["subscription"]["user_id"] == "firebase-user-a"
    assert FakePushService.records["token-value-long-enough-12345"] == "firebase-user-a"


def test_other_user_cannot_test_or_remove_owned_token(monkeypatch) -> None:
    token = "owned-token-value-long-enough-123"
    FakePushService.records = {token: "firebase-user-a"}
    monkeypatch.setattr(push_routes, "PushNotificationService", FakePushService)
    app.dependency_overrides[current_user] = lambda: _as_user("firebase-user-b")
    try:
        test_response = client.post("/api/push/test", json={"token": token})
        delete_response = client.request("DELETE", "/api/push/tokens", json={"token": token})
    finally:
        app.dependency_overrides.clear()

    assert test_response.status_code == 404
    assert delete_response.status_code == 200
    assert delete_response.json() == {"ok": False}
    assert FakePushService.records[token] == "firebase-user-a"


def test_owner_can_remove_owned_token(monkeypatch) -> None:
    token = "owner-token-value-long-enough-123"
    FakePushService.records = {token: "firebase-user-a"}
    monkeypatch.setattr(push_routes, "PushNotificationService", FakePushService)
    app.dependency_overrides[current_user] = lambda: _as_user("firebase-user-a")
    try:
        response = client.request("DELETE", "/api/push/tokens", json={"token": token})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert token not in FakePushService.records


def test_push_token_routes_require_authentication() -> None:
    response = client.post(
        "/api/push/tokens",
        json={"token": "token-value-long-enough-12345"},
    )
    assert response.status_code == 401
