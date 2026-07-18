from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import user_data_routes
from app.api.enterprise_admin_routes import AuthContext


class FakeUserDataService:
    def __init__(self):
        self.saved = []
        self.cooked = []
        self.interactions = []
        self.cooking_sessions = []
        self.preferences = {}

    def save_recipe(self, enterprise_id, uid, recipe):
        record = {**recipe, "id": recipe.get("id", "recipe-1")}
        self.saved.append(record)
        return record

    def list_recipes(self, enterprise_id, uid):
        return self.saved

    def delete_recipe(self, enterprise_id, uid, recipe_id):
        return True

    def add_recent(self, enterprise_id, uid, recipe):
        return {**recipe, "recent_id": "recent-1"}

    def list_recents(self, enterprise_id, uid, limit=20):
        return []

    def record_cooked(self, enterprise_id, uid, payload, profile_id=None):
        record = {**payload, "id": "history-1", "profile_id": profile_id or "default"}
        self.cooked.append(record)
        return record

    def list_cooked(self, enterprise_id, uid, limit=50, profile_id=None):
        return self.cooked

    def create_cooking_session(self, enterprise_id, uid, payload, profile_id=None):
        record = {
            **payload,
            "id": f"session-{len(self.cooking_sessions) + 1}",
            "profile_id": profile_id or "default",
            "status": "active",
        }
        self.cooking_sessions.append(record)
        return record

    def active_cooking_session(self, enterprise_id, uid, profile_id=None):
        return next((item for item in reversed(self.cooking_sessions) if item["status"] == "active"), None)

    def update_cooking_session(self, enterprise_id, uid, session_id, updates, profile_id=None):
        session = next((item for item in self.cooking_sessions if item["id"] == session_id), None)
        if session is None:
            return None
        session.update(updates)
        return session

    def record_recipe_interaction(self, enterprise_id, uid, payload, profile_id=None):
        record = {**payload, "id": f"interaction-{len(self.interactions) + 1}", "profile_id": profile_id or "default"}
        self.interactions.append(record)
        return record

    def list_recipe_interactions(self, enterprise_id, uid, limit=100, profile_id=None):
        return self.interactions[:limit]

    def flavor_memory_summary(self, enterprise_id, uid, profile_id=None):
        counts = {key: 0 for key in ("cooked", "dismissed", "repeated", "saved")}
        for interaction in self.interactions:
            counts[interaction["interaction_type"]] += 1
        return {
            "profile_id": profile_id or "default",
            "total_interactions": len(self.interactions),
            "counts": counts,
            "repeat_favorites": [],
        }

    def save_preferences(self, enterprise_id, uid, preferences, profile_id=None):
        self.preferences.update(preferences)
        return self.preferences

    def get_preferences(self, enterprise_id, uid, profile_id=None):
        return self.preferences


def authenticated_client(monkeypatch):
    fake = FakeUserDataService()
    monkeypatch.setattr(user_data_routes, "service", lambda: fake)

    app = FastAPI()
    app.include_router(user_data_routes.router)
    app.dependency_overrides[user_data_routes.current_user] = lambda: AuthContext(
        uid="firebase-user-1",
        enterprise_id="glucoplate",
        role="member",
    )
    return TestClient(app), fake


def test_user_data_is_scoped_to_authenticated_enterprise(monkeypatch):
    client, _fake = authenticated_client(monkeypatch)

    saved = client.post("/api/user-data/recipes", json={"recipe": {"name": "Mangú"}})
    assert saved.status_code == 200
    assert saved.json()["recipe"]["name"] == "Mangú"

    cooked = client.post(
        "/api/user-data/cooking-history",
        json={"recipe_name": "Mangú", "rating": 5, "notes": "Family favorite"},
    )
    assert cooked.status_code == 200
    assert cooked.json()["history"]["rating"] == 5

    preferences = client.put(
        "/api/user-data/preferences",
        json={"preferences": {"servings": 4, "culture": "Dominican"}},
    )
    assert preferences.status_code == 200
    assert preferences.json()["preferences"]["culture"] == "Dominican"


def test_recipe_interactions_build_flavor_memory(monkeypatch):
    client, _fake = authenticated_client(monkeypatch)

    dismissed = client.post(
        "/api/user-data/recipe-interactions",
        json={
            "interaction_type": "dismissed",
            "recipe_id": "recipe-1",
            "recipe_name": "Plain oatmeal",
            "source": "generation-results",
            "profile_id": "luna",
        },
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["interaction"]["profile_id"] == "luna"

    repeated = client.post(
        "/api/user-data/recipe-interactions",
        json={
            "interaction_type": "repeated",
            "recipe_id": "recipe-2",
            "recipe_name": "Mangú",
            "rating": 5,
            "profile_id": "luna",
        },
    )
    assert repeated.status_code == 200

    listed = client.get("/api/user-data/recipe-interactions?profile_id=luna")
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    memory = client.get("/api/user-data/flavor-memory?profile_id=luna")
    assert memory.status_code == 200
    assert memory.json()["total_interactions"] == 2
    assert memory.json()["counts"]["dismissed"] == 1
    assert memory.json()["counts"]["repeated"] == 1


def test_recipe_interaction_type_is_validated(monkeypatch):
    client, _fake = authenticated_client(monkeypatch)

    response = client.post(
        "/api/user-data/recipe-interactions",
        json={"interaction_type": "viewed", "recipe_name": "Mangú"},
    )

    assert response.status_code == 422


def test_user_without_enterprise_is_rejected(monkeypatch):
    monkeypatch.setattr(user_data_routes, "service", FakeUserDataService)
    app = FastAPI()
    app.include_router(user_data_routes.router)
    app.dependency_overrides[user_data_routes.current_user] = lambda: AuthContext(uid="user-without-company")

    response = TestClient(app).get("/api/user-data/recipes")
    assert response.status_code == 403


def test_private_cooking_session_create_progress_and_complete(monkeypatch):
    client, fake = authenticated_client(monkeypatch)

    created = client.post(
        "/api/user-data/cooking-sessions",
        json={
            "recipe_id": "recipe-1",
            "recipe_name": "Mangú",
            "recipe": {"id": "recipe-1", "title": "Mangú", "steps": ["Boil", "Mash"]},
            "profile_id": "luna",
        },
    )
    assert created.status_code == 201
    session = created.json()["session"]
    assert session["status"] == "active"
    assert session["profile_id"] == "luna"

    active = client.get("/api/user-data/cooking-sessions/active?profile_id=luna")
    assert active.status_code == 200
    assert active.json()["session"]["id"] == session["id"]

    progressed = client.patch(
        f"/api/user-data/cooking-sessions/{session['id']}",
        json={"current_step": 1, "completed_steps": [0], "profile_id": "luna"},
    )
    assert progressed.status_code == 200
    assert progressed.json()["session"]["current_step"] == 1

    completed = client.patch(
        f"/api/user-data/cooking-sessions/{session['id']}",
        json={"status": "completed", "completed_steps": [0, 1], "profile_id": "luna"},
    )
    assert completed.status_code == 200
    assert completed.json()["session"]["status"] == "completed"
    assert fake.active_cooking_session("glucoplate", "firebase-user-1", "luna") is None


def test_unknown_private_cooking_session_returns_404(monkeypatch):
    client, _fake = authenticated_client(monkeypatch)
    response = client.patch(
        "/api/user-data/cooking-sessions/missing",
        json={"current_step": 1},
    )
    assert response.status_code == 404
