from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import enterprise_admin_routes
from app.main import app


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


class FakeDirectory:
    def list_members(self, enterprise_id: str) -> list[dict]:
        assert enterprise_id == "glucoplate"
        return [
            {
                "user_id": "firebase-user-1",
                "email": "owner@example.com",
                "display_name": "Enterprise Owner",
                "role": "enterprise_owner",
                "status": "active",
                "last_login_at": "2026-07-16T12:00:00+00:00",
            },
            {
                "user_id": "firebase-user-2",
                "email": "member@example.com",
                "display_name": "Team Member",
                "role": "member",
                "status": "active",
                "last_login_at": "2026-07-16T11:00:00+00:00",
            },
        ]


def test_enterprise_admin_can_load_synchronized_users(monkeypatch) -> None:
    monkeypatch.setattr(enterprise_admin_routes, "directory", lambda: FakeDirectory())
    app.dependency_overrides[enterprise_admin_routes.current_user] = lambda: enterprise_admin_routes.AuthContext(
        uid="firebase-user-1",
        email="owner@example.com",
        enterprise_id="glucoplate",
        enterprise_name="GlucoPlate AI",
        role="enterprise_owner",
    )
    try:
        response = client.get("/api/enterprise/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["enterprise_id"] == "glucoplate"
    assert [user["user_id"] for user in payload["users"]] == ["firebase-user-1", "firebase-user-2"]


def test_regular_member_is_denied_admin_user_listing() -> None:
    app.dependency_overrides[enterprise_admin_routes.current_user] = lambda: enterprise_admin_routes.AuthContext(
        uid="firebase-user-2",
        email="member@example.com",
        enterprise_id="glucoplate",
        role="member",
    )
    try:
        response = client.get("/api/enterprise/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "administrator permission" in response.json()["detail"].lower()


def test_admin_without_enterprise_is_denied_user_listing() -> None:
    app.dependency_overrides[enterprise_admin_routes.current_user] = lambda: enterprise_admin_routes.AuthContext(
        uid="firebase-user-3",
        email="admin@example.com",
        role="enterprise_admin",
    )
    try:
        response = client.get("/api/enterprise/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "enterprise membership" in response.json()["detail"].lower()


def test_admin_dashboard_client_loads_and_renders_enterprise_users() -> None:
    html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
    script = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")

    assert "GlucoPlate Enterprise Admin" in html
    assert 'id="userRows"' in html
    assert 'id="usersEmpty"' in html
    assert "/api/enterprise/admin/users" in script
    assert "renderUsers" in script
    assert "result.users||[]" in script
    assert "filtered.length>0" in script
