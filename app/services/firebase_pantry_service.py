from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebasePantryService:
    """Persist profile-scoped pantry inventory in Firebase Realtime Database."""

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

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if value is not None}

    def _pantry_root(self, enterprise_id: str, uid: str, profile_id: str | None):
        selected_profile_id = self._profile_id(profile_id)
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/users/{uid}/profiles/"
            f"{selected_profile_id}/pantry_items"
        )

    def create_item(
        self,
        enterprise_id: str,
        uid: str,
        payload: dict[str, Any],
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        item_id = uuid.uuid4().hex
        selected_profile_id = self._profile_id(profile_id or payload.get("profile_id"))
        now = self._now()
        record = self._normalize({
            **payload,
            "id": item_id,
            "profile_id": selected_profile_id,
            "name": str(payload.get("name") or "").strip(),
            "created_at": now,
            "updated_at": now,
        })
        self._pantry_root(enterprise_id, uid, selected_profile_id).child(item_id).set(record)
        return self._with_expiration_status(record)

    def list_items(
        self,
        enterprise_id: str,
        uid: str,
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self._pantry_root(enterprise_id, uid, profile_id).get() or {}
        items = [self._with_expiration_status(item) for item in data.values()]
        return sorted(
            items,
            key=lambda item: (
                item.get("days_until_expiration") is None,
                item.get("days_until_expiration") if item.get("days_until_expiration") is not None else 999999,
                str(item.get("name") or "").lower(),
            ),
        )

    def get_item(
        self,
        enterprise_id: str,
        uid: str,
        item_id: str,
        profile_id: str | None = None,
    ) -> dict[str, Any] | None:
        item = self._pantry_root(enterprise_id, uid, profile_id).child(item_id).get()
        return self._with_expiration_status(item) if item else None

    def update_item(
        self,
        enterprise_id: str,
        uid: str,
        item_id: str,
        payload: dict[str, Any],
        profile_id: str | None = None,
    ) -> dict[str, Any] | None:
        selected_profile_id = self._profile_id(profile_id or payload.get("profile_id"))
        ref = self._pantry_root(enterprise_id, uid, selected_profile_id).child(item_id)
        existing = ref.get()
        if existing is None:
            return None
        record = self._normalize({
            **existing,
            **payload,
            "id": item_id,
            "profile_id": selected_profile_id,
            "name": str(payload.get("name", existing.get("name", ""))).strip(),
            "updated_at": self._now(),
        })
        ref.set(record)
        return self._with_expiration_status(record)

    def delete_item(
        self,
        enterprise_id: str,
        uid: str,
        item_id: str,
        profile_id: str | None = None,
    ) -> bool:
        ref = self._pantry_root(enterprise_id, uid, profile_id).child(item_id)
        if ref.get() is None:
            return False
        ref.delete()
        return True

    @staticmethod
    def _with_expiration_status(item: dict[str, Any]) -> dict[str, Any]:
        record = dict(item)
        expiration_date = record.get("expiration_date")
        if not expiration_date:
            record["days_until_expiration"] = None
            record["expiration_status"] = "unknown"
            return record
        try:
            expires = date.fromisoformat(str(expiration_date))
        except ValueError:
            record["days_until_expiration"] = None
            record["expiration_status"] = "unknown"
            return record

        days = (expires - datetime.now(UTC).date()).days
        record["days_until_expiration"] = days
        if days < 0:
            record["expiration_status"] = "expired"
        elif days <= 2:
            record["expiration_status"] = "use_soon"
        else:
            record["expiration_status"] = "fresh"
        return record
