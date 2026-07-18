from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookSessionLifecycleService:
    """Manage the authoritative waiting, active, and completed room phases."""

    ROOT = "app_data"

    def __init__(self) -> None:
        firebase = FirebaseAuthService()
        self.app = firebase._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _room(self, enterprise_id: str, room_id: str):
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_rooms/{room_id}",
            app=self.app,
        )

    @staticmethod
    def phase(room: dict[str, Any]) -> str:
        return str((room.get("state") or {}).get("session_status") or "waiting")

    def initialize_waiting(self, enterprise_id: str, room_id: str) -> None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get() or {}
        state = room.get("state") or {}
        state.update(
            {
                "session_status": "waiting",
                "started_at": None,
                "completed_at": None,
                "started_by": None,
                "completed_by": None,
            }
        )
        room_ref.child("state").set(state)

    def transition(
        self,
        enterprise_id: str,
        room_id: str,
        actor_uid: str,
        target: str,
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        if not room:
            return None
        if str(room.get("host_uid")) != str(actor_uid):
            raise PermissionError("Only the room host can change the cooking session phase")

        state = room.get("state") or {}
        current = self.phase(room)
        if target == "active":
            if current != "waiting":
                raise ValueError("Only a waiting room can be started")
            now = self._now()
            state.update(
                {
                    "session_status": "active",
                    "started_at": now,
                    "started_by": actor_uid,
                    "revision": int(state.get("revision") or 0) + 1,
                    "updated_at": now,
                    "updated_by": actor_uid,
                }
            )
            room_ref.child("state").set(state)
            room_ref.update({"updated_at": now})
        elif target == "completed":
            if current != "active":
                raise ValueError("Only an active cooking session can be completed")
            now = self._now()
            state.update(
                {
                    "session_status": "completed",
                    "completed_at": now,
                    "completed_by": actor_uid,
                    "revision": int(state.get("revision") or 0) + 1,
                    "updated_at": now,
                    "updated_by": actor_uid,
                }
            )
            room_ref.child("state").set(state)
            room_ref.update({"updated_at": now, "status": "completed"})
        else:
            raise ValueError("Unsupported cooking session phase")

        return room_ref.get()
