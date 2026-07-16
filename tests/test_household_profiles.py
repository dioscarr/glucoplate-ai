from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.enterprise_admin_routes import AuthContext, current_user
from app.api import user_data_routes
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


class FakeUserDataService:
    def __init__(self) -> None:
        self.profiles: dict[str, dict] = {}
        self.preferences: dict[str, dict] = {}
        self.history: dict[str, list[dict]] = {}

    def create_profile(self, enterprise_id: str, uid: str, profile: dict) -> dict:
        record = {**profile, "id": "profile-luna"}
        self.profiles[record["id"]] = record
        return record

    def list_profiles(self, enterprise_id: str, uid: str) -> list[dict]:
        return list(self.profiles.values())

    def delete_profile(self, enterprise_id: str, uid: str, profile_id: str) -> bool:
        return self.profiles.pop(profile_id, None) is not None

    def save_preferences(self, enterprise_id: str, uid: str, preferences: dict, profile_id: str | None = None) -> dict:
        self.preferences[profile_id or "default"] = preferences
        return preferences

    def get_preferences(self, enterprise_id: str, uid: str, profile_id: str | None = None) -> dict:
        return self.preferences.get(profile_id or "default", {})

    def record_cooked(self, enterprise_id: str, uid: str, payload: dict, profile_id: str | None = None) -> dict:
        selected = profile_id or "default"
        record = {**payload, "id": "history-1", "profile_id": selected}
        self.history.setdefault(selected, []).append(record)
        return record

    def list_cooked(self, enterprise_id: str, uid: str, limit: int = 50, profile_id: str | None = None) -> list[dict]:
        return self.history.get(profile_id or "default", [])[:limit]


fake = FakeUserDataService()


def enterprise_user() -> AuthContext:
    return AuthContext(uid="firebase-user", email="family@example.com", enterprise_id="glucoplate", role="member")


def setup_function() -> None:
    fake.profiles.clear()
    fake.preferences.clear()
    fake.history.clear()
    app.dependency_overrides[current_user] = enterprise_user
    app.dependency_overrides[user_data_routes.scoped_user] = enterprise_user
    user_data_routes.service = lambda: fake


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_profile_creation_and_listing_are_user_scoped() -> None:
    created = client.post(
        "/api/user-data/profiles",
        json={"name": "Luna", "avatar": "🌙", "relationship": "child", "allergies": ["peanuts"]},
    )
    assert created.status_code == 200
    assert created.json()["profile"]["id"] == "profile-luna"

    listed = client.get("/api/user-data/profiles")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Luna"
    assert listed.json()[0]["allergies"] == ["peanuts"]


def test_preferences_and_history_are_isolated_by_active_profile() -> None:
    save = client.put(
        "/api/user-data/preferences",
        json={"profile_id": "profile-luna", "preferences": {"avoid": ["spicy"], "servings": 1}},
    )
    assert save.status_code == 200

    assert client.get("/api/user-data/preferences?profile_id=profile-luna").json()["servings"] == 1
    assert client.get("/api/user-data/preferences?profile_id=default").json() == {}

    cooked = client.post(
        "/api/user-data/cooking-history",
        json={"profile_id": "profile-luna", "recipe_name": "Mangú", "rating": 5},
    )
    assert cooked.status_code == 200
    assert cooked.json()["history"]["profile_id"] == "profile-luna"
    assert len(client.get("/api/user-data/cooking-history?profile_id=profile-luna").json()) == 1
    assert client.get("/api/user-data/cooking-history?profile_id=default").json() == []


def test_household_profile_client_tracks_active_profile() -> None:
    script = (ROOT / "app" / "static" / "firebase-user-data.js").read_text(encoding="utf-8")
    assert "glucoplate_active_profile_id" in script
    assert "listProfiles" in script
    assert "createProfile" in script
    assert "setActiveProfile" in script
    assert "profile_id" in script
