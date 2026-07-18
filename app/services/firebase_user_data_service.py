from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebaseUserDataService:
    """Persist user-scoped GlucoPlate data in Firebase Realtime Database."""

    ROOT = "app_data"
    DEFAULT_PROFILE_ID = "default"
    INTERACTION_TYPES = {"saved", "cooked", "dismissed", "repeated"}

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if value is not None}

    @classmethod
    def _profile_id(cls, profile_id: str | None) -> str:
        value = str(profile_id or cls.DEFAULT_PROFILE_ID).strip()
        return value or cls.DEFAULT_PROFILE_ID

    def _user_root(self, enterprise_id: str, uid: str):
        return db.reference(f"{self.ROOT}/enterprises/{enterprise_id}/users/{uid}")

    def _profile_root(self, enterprise_id: str, uid: str, profile_id: str | None):
        return self._user_root(enterprise_id, uid).child(f"profiles/{self._profile_id(profile_id)}")

    def create_profile(self, enterprise_id: str, uid: str, profile: dict[str, Any]) -> dict[str, Any]:
        profile_id = str(profile.get("id") or uuid.uuid4().hex)
        now = self._now()
        record = self._normalize({
            **profile,
            "id": profile_id,
            "name": str(profile.get("name") or "Household member").strip(),
            "created_at": profile.get("created_at") or now,
            "updated_at": now,
        })
        self._profile_root(enterprise_id, uid, profile_id).update(record)
        return record

    def list_profiles(self, enterprise_id: str, uid: str) -> list[dict[str, Any]]:
        data = self._user_root(enterprise_id, uid).child("profiles").get() or {}
        return sorted(data.values(), key=lambda item: (item.get("name", "").lower(), item.get("created_at", "")))

    def get_profile(self, enterprise_id: str, uid: str, profile_id: str) -> dict[str, Any] | None:
        return self._profile_root(enterprise_id, uid, profile_id).get()

    def delete_profile(self, enterprise_id: str, uid: str, profile_id: str) -> bool:
        if self._profile_id(profile_id) == self.DEFAULT_PROFILE_ID:
            return False
        ref = self._profile_root(enterprise_id, uid, profile_id)
        if ref.get() is None:
            return False
        ref.delete()
        return True

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
        record = {"id": generation_id, "request": request, "recipe": recipe, "generated_at": self._now()}
        self._user_root(enterprise_id, uid).child(f"recipe_generations/{generation_id}").set(record)
        return record

    def record_cooked(self, enterprise_id: str, uid: str, payload: dict[str, Any], profile_id: str | None = None) -> dict[str, Any]:
        history_id = uuid.uuid4().hex
        now = self._now()
        selected_profile_id = self._profile_id(profile_id or payload.get("profile_id"))
        record = self._normalize({
            **payload,
            "id": history_id,
            "profile_id": selected_profile_id,
            "cooked_at": payload.get("cooked_at") or now,
            "created_at": now,
        })
        self._profile_root(enterprise_id, uid, selected_profile_id).child(f"cooking_history/{history_id}").set(record)
        return record

    def list_cooked(self, enterprise_id: str, uid: str, limit: int = 50, profile_id: str | None = None) -> list[dict[str, Any]]:
        data = self._profile_root(enterprise_id, uid, profile_id).child("cooking_history").get() or {}
        items = sorted(data.values(), key=lambda item: item.get("cooked_at", ""), reverse=True)
        return items[: max(1, min(limit, 200))]

    def record_recipe_interaction(
        self,
        enterprise_id: str,
        uid: str,
        payload: dict[str, Any],
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        interaction_type = str(payload.get("interaction_type") or "").strip().lower()
        if interaction_type not in self.INTERACTION_TYPES:
            raise ValueError(f"Unsupported interaction type: {interaction_type}")

        interaction_id = uuid.uuid4().hex
        selected_profile_id = self._profile_id(profile_id or payload.get("profile_id"))
        now = self._now()
        record = self._normalize({
            **payload,
            "id": interaction_id,
            "interaction_type": interaction_type,
            "profile_id": selected_profile_id,
            "occurred_at": payload.get("occurred_at") or now,
            "created_at": now,
        })
        self._profile_root(enterprise_id, uid, selected_profile_id).child(
            f"recipe_interactions/{interaction_id}"
        ).set(record)
        return record

    def list_recipe_interactions(
        self,
        enterprise_id: str,
        uid: str,
        limit: int = 100,
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self._profile_root(enterprise_id, uid, profile_id).child("recipe_interactions").get() or {}
        items = sorted(data.values(), key=lambda item: item.get("occurred_at", ""), reverse=True)
        return items[: max(1, min(limit, 500))]

    def flavor_memory_summary(
        self,
        enterprise_id: str,
        uid: str,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        interactions = self.list_recipe_interactions(enterprise_id, uid, 500, profile_id)
        counts = Counter(item.get("interaction_type") for item in interactions)
        recipe_counts = Counter(
            str(item.get("recipe_id") or item.get("recipe_name") or "").strip()
            for item in interactions
            if item.get("interaction_type") in {"cooked", "repeated"}
            and str(item.get("recipe_id") or item.get("recipe_name") or "").strip()
        )
        return {
            "profile_id": self._profile_id(profile_id),
            "total_interactions": len(interactions),
            "counts": {interaction_type: counts.get(interaction_type, 0) for interaction_type in sorted(self.INTERACTION_TYPES)},
            "repeat_favorites": [
                {"recipe_key": recipe_key, "count": count}
                for recipe_key, count in recipe_counts.most_common(5)
            ],
        }

    def save_preferences(self, enterprise_id: str, uid: str, preferences: dict[str, Any], profile_id: str | None = None) -> dict[str, Any]:
        record = self._normalize({**preferences, "updated_at": self._now()})
        self._profile_root(enterprise_id, uid, profile_id).child("preferences").update(record)
        return self.get_preferences(enterprise_id, uid, profile_id)

    def get_preferences(self, enterprise_id: str, uid: str, profile_id: str | None = None) -> dict[str, Any]:
        return self._profile_root(enterprise_id, uid, profile_id).child("preferences").get() or {}
