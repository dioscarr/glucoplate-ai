from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebaseShoppingListService:
    """Persist profile-scoped shopping list items in Firebase Realtime Database."""

    ROOT = "app_data"
    DEFAULT_PROFILE_ID = "default"

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @classmethod
    def _profile_id(cls, profile_id: str | None) -> str:
        value = str(profile_id or cls.DEFAULT_PROFILE_ID).strip()
        return value or cls.DEFAULT_PROFILE_ID

    def _root(self, enterprise_id: str, uid: str, profile_id: str | None):
        selected = self._profile_id(profile_id)
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/users/{uid}/profiles/{selected}/shopping_list_items"
        )

    def add_items(
        self,
        enterprise_id: str,
        uid: str,
        items: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        selected = self._profile_id(profile_id)
        root = self._root(enterprise_id, uid, selected)
        existing = root.get() or {}
        existing_names = {
            str(item.get("name") or "").strip().lower()
            for item in existing.values()
            if str(item.get("name") or "").strip()
        }
        created: list[dict[str, Any]] = []
        for payload in items:
            name = str(payload.get("name") or "").strip()
            if not name or name.lower() in existing_names:
                continue
            item_id = uuid.uuid4().hex
            now = self._now()
            record = {
                "id": item_id,
                "profile_id": selected,
                "name": name,
                "quantity": payload.get("quantity"),
                "unit": payload.get("unit"),
                "source_recipe": payload.get("source_recipe"),
                "checked": False,
                "created_at": now,
                "updated_at": now,
            }
            record = {key: value for key, value in record.items() if value is not None}
            root.child(item_id).set(record)
            existing_names.add(name.lower())
            created.append(record)
        return created

    def list_items(self, enterprise_id: str, uid: str, profile_id: str | None = None) -> list[dict[str, Any]]:
        data = self._root(enterprise_id, uid, profile_id).get() or {}
        return sorted(
            data.values(),
            key=lambda item: (bool(item.get("checked")), str(item.get("created_at") or ""), str(item.get("name") or "").lower()),
        )

    def update_item(
        self,
        enterprise_id: str,
        uid: str,
        item_id: str,
        payload: dict[str, Any],
        profile_id: str | None = None,
    ) -> dict[str, Any] | None:
        selected = self._profile_id(profile_id or payload.get("profile_id"))
        ref = self._root(enterprise_id, uid, selected).child(item_id)
        existing = ref.get()
        if existing is None:
            return None
        record = {
            **existing,
            **{key: value for key, value in payload.items() if value is not None},
            "id": item_id,
            "profile_id": selected,
            "updated_at": self._now(),
        }
        ref.set(record)
        return record

    def delete_item(self, enterprise_id: str, uid: str, item_id: str, profile_id: str | None = None) -> bool:
        ref = self._root(enterprise_id, uid, profile_id).child(item_id)
        if ref.get() is None:
            return False
        ref.delete()
        return True

    def clear_checked(self, enterprise_id: str, uid: str, profile_id: str | None = None) -> int:
        root = self._root(enterprise_id, uid, profile_id)
        data = root.get() or {}
        removed = 0
        for item_id, item in data.items():
            if item.get("checked"):
                root.child(item_id).delete()
                removed += 1
        return removed
