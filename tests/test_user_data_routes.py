from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import user_data_routes
from app.api.enterprise_admin_routes import AuthContext


class FakeUserDataService:
    def __init__(self):
        self.saved = []
        self.cooked = []
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

    def record_cooked(self, enterprise_id, uid, payload):
        record = {**payload, "id": "history-1"}
        self.cooked.append(record)
        return record

    def list_cooked(self, enterprise_id, uid, limit=50):
        return self.cooked

    def save_preferences(self, enterprise_id, uid, preferences):
        self.preferences.update(preferences)
        return self.preferences

    def get_preferences(self, enterprise_id, uid):
        return self.preferences


def test_user_data_is_scoped_to_authenticated_enterprise(monkeypatch):
    fake = FakeUserDataService()
    monkeypatch.setattr(user_data_routes, "service", lambda: fake)

    app = FastAPI()
    app.include_router(user_data_routes.router)
    app.dependency_overrides[user_data_routes.current_user] = lambda: AuthContext(
        uid="firebase-user-1",
        enterprise_id="glucoplate",
        role="member",
    )
    client = TestClient(app)

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


def test_user_without_enterprise_is_rejected(monkeypatch):
    monkeypatch.setattr(user_data_routes, "service", FakeUserDataService)
    app = FastAPI()
    app.include_router(user_data_routes.router)
    app.dependency_overrides[user_data_routes.current_user] = lambda: AuthContext(uid="user-without-company")

    response = TestClient(app).get("/api/user-data/recipes")
    assert response.status_code == 403
