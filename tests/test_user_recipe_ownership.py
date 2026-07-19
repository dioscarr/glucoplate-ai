from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import user_data_routes
from app.api.enterprise_admin_routes import AuthContext
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class FakeUserDataService:
    def __init__(self) -> None:
        self.recipes: dict[tuple[str, str], dict[str, dict]] = {}

    def save_recipe(self, enterprise_id: str, uid: str, recipe: dict) -> dict:
        record = {**recipe, "id": str(recipe.get("id") or "generated-id")}
        self.recipes.setdefault((enterprise_id, uid), {})[record["id"]] = record
        return record

    def list_recipes(self, enterprise_id: str, uid: str) -> list[dict]:
        return list(self.recipes.get((enterprise_id, uid), {}).values())

    def delete_recipe(self, enterprise_id: str, uid: str, recipe_id: str) -> bool:
        scoped = self.recipes.get((enterprise_id, uid), {})
        return scoped.pop(recipe_id, None) is not None


def _user(uid: str, enterprise_id: str = "glucoplate") -> AuthContext:
    return AuthContext(uid=uid, email=f"{uid}@example.com", enterprise_id=enterprise_id, role="member")


def test_saved_recipes_are_isolated_by_authenticated_user() -> None:
    store = FakeUserDataService()
    app.dependency_overrides[user_data_routes.service] = lambda: store

    try:
        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("user-a")
        saved = client.post(
            "/api/user-data/recipes",
            json={"recipe": {"id": "recipe-a", "title": "User A Recipe"}},
        )
        assert saved.status_code == 200

        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("user-b")
        listed_for_b = client.get("/api/user-data/recipes")
        assert listed_for_b.status_code == 200
        assert listed_for_b.json() == []

        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("user-a")
        listed_for_a = client.get("/api/user-data/recipes")
        assert listed_for_a.status_code == 200
        assert [recipe["id"] for recipe in listed_for_a.json()] == ["recipe-a"]
    finally:
        app.dependency_overrides.clear()


def test_user_cannot_delete_another_users_saved_recipe() -> None:
    store = FakeUserDataService()
    store.save_recipe("glucoplate", "user-a", {"id": "private-recipe", "title": "Private"})
    app.dependency_overrides[user_data_routes.service] = lambda: store

    try:
        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("user-b")
        denied = client.delete("/api/user-data/recipes/private-recipe")
        assert denied.status_code == 404

        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("user-a")
        owner_list = client.get("/api/user-data/recipes")
        assert [recipe["id"] for recipe in owner_list.json()] == ["private-recipe"]
    finally:
        app.dependency_overrides.clear()


def test_saved_recipes_are_isolated_by_enterprise() -> None:
    store = FakeUserDataService()
    store.save_recipe("enterprise-a", "shared-uid", {"id": "enterprise-a-recipe", "title": "A"})
    app.dependency_overrides[user_data_routes.service] = lambda: store

    try:
        app.dependency_overrides[user_data_routes.scoped_user] = lambda: _user("shared-uid", "enterprise-b")
        listed = client.get("/api/user-data/recipes")
        assert listed.status_code == 200
        assert listed.json() == []
    finally:
        app.dependency_overrides.clear()


def test_recipe_routes_require_enterprise_membership() -> None:
    app.dependency_overrides[user_data_routes.current_user] = lambda: AuthContext(uid="personal-user")

    try:
        response = client.get("/api/user-data/recipes")
        assert response.status_code == 403
        assert response.json()["detail"] == "Enterprise membership is required"
    finally:
        app.dependency_overrides.clear()
