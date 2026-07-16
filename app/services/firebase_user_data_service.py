from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebaseUserDataService:
    """Persist user-scoped GlucoPlate data in Firebase Realtime Database."""

    ROOT = "app_data"

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if value is not None}

    def _user_root(self, enterprise_id: str, uid: str):
        return db.reference(f"{self.ROOT}/enterprises/{enterprise_id}/users/{uid}")

    def save_recipe(self, enterprise_id: str, uid: str, recipe: dict[str, Any]) -> dict[str, Any]:
        recipe_id = str(recipe.get("id") or recipe.get("recipe_id") or uuid.uuid4().hex)
        now = self._now()
        record = self._normalize({**recipe, "id": recipe_id, "saved_at": recipe.get("saved_at") or now, "updated_at": now})
        self._user_root(enterprise_id, uid).child(f"saved_recipes/{recipe_id}").set(record)
        return record

    def list_recipes(self, enterprise_id: str, uid: str) -> list[dict[str, Any]]:
        data = self._user_root(enterprise_id, uid).child("saved_recipes").get() or {}
        return sorted(data.values(), key=lambda item: item.get("saved_at", ""), reverse=True)

    def delete_recipe(self, enterprise_id: str, uid: str, recipe_id: str) -> bool:
        ref = self._user_root(enterprise_id, uid).child(f"saved_recipes/{recipe_id}")
        if ref.get() is None:
            return False
        ref.delete()
        return True

    def add_recent(self, enterprise_id: str, uid: str, recipe: dict[str, Any]) -> dict[str, Any]:
        recent_id = uuid.uuid4().hex
        record = self._normalize({**recipe, "recent_id": recent_id, "viewed_at": self._now()})
        self._user_root(enterprise_id, uid).child(f"recent_recipes/{recent_id}").set(record)
        return record

    def list_recents(self, enterprise_id: str, uid: str, limit: int = 20) -> list[dict[str, Any]]:
        data = self._user_root(enterprise_id, uid).child("recent_recipes").get() or {}
        items = sorted(data.values(), key=lambda item: item.get("viewed_at", ""), reverse=True)
        return items[: max(1, min(limit, 100))]

    def record_generation(self, enterprise_id: str, uid: str, request: dict[str, Any], recipe: dict[str, Any]) -> dict[str, Any]:
        generation_id = uuid.uuid4().hex
        record = {
            "id": generation_id,
            "request": request,
            "recipe": recipe,
            "generated_at": self._now(),
        }
        self._user_root(enterprise_id, uid).child(f"recipe_generations/{generation_id}").set(record)
        return record

    def record_cooked(self, enterprise_id: str, uid: str, payload: dict[str, Any]) -> dict[str, Any]:
        history_id = uuid.uuid4().hex
        now = self._now()
        record = self._normalize({
            **payload,
            "id": history_id,
            "cooked_at": payload.get("cooked_at") or now,
            "created_at": now,
        })
        self._user_root(enterprise_id, uid).child(f"cooking_history/{history_id}").set(record)
        return record

    def list_cooked(self, enterprise_id: str, uid: str, limit: int = 50) -> list[dict[str, Any]]:
        data = self._user_root(enterprise_id, uid).child("cooking_history").get() or {}
        items = sorted(data.values(), key=lambda item: item.get("cooked_at", ""), reverse=True)
        return items[: max(1, min(limit, 200))]

    def save_preferences(self, enterprise_id: str, uid: str, preferences: dict[str, Any]) -> dict[str, Any]:
        record = self._normalize({**preferences, "updated_at": self._now()})
        self._user_root(enterprise_id, uid).child("preferences").update(record)
        return self.get_preferences(enterprise_id, uid)

    def get_preferences(self, enterprise_id: str, uid: str) -> dict[str, Any]:
        return self._user_root(enterprise_id, uid).child("preferences").get() or {}
