from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookMediaService:
    """Authorize and persist optional media state beside the cooking room."""

    ROOT = "app_data"

    def __init__(self) -> None:
        self.app = FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _room(self, enterprise_id: str, room_id: str):
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_rooms/{room_id}",
            app=self.app,
        )

    def access(self, enterprise_id: str, room_id: str, uid: str) -> dict[str, Any] | None:
        room = self._room(enterprise_id, room_id).get()
        participants = (room or {}).get("participants") or {}
        if not room or uid not in participants:
            return None
        phase = str((room.get("state") or {}).get("session_status") or "waiting")
        if room.get("status") == "completed" or phase == "completed":
            raise ValueError("Media is unavailable after the cooking session is completed")
        provider = str(os.getenv("LIVE_COOK_MEDIA_PROVIDER", "browser")).strip().lower() or "browser"
        participant = participants.get(uid) or {}
        return {
            "room_id": room_id,
            "provider": provider,
            "mode": "local-preview" if provider == "browser" else "provider",
            "remote_enabled": provider not in {"browser", "disabled"},
            "participant": {
                "uid": uid,
                "role": participant.get("role") or "participant",
                "display_name": participant.get("display_name") or "Cook",
            },
            "recording": {"enabled": False, "consent_required": True},
            "fallback": "The synchronized cooking room remains available without media.",
        }

    def update_state(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        state: dict[str, Any],
    ) -> dict[str, Any] | None:
        access = self.access(enterprise_id, room_id, uid)
        if access is None:
            return None
        allowed = {
            key: value
            for key, value in state.items()
            if key in {"camera_enabled", "microphone_enabled", "connection_state"}
        }
        record = {
            **allowed,
            "uid": uid,
            "provider": access["provider"],
            "updated_at": self._now(),
        }
        self._room(enterprise_id, room_id).child("media").child("participants").child(uid).set(record)
        return record
