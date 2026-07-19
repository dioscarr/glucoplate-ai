from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookSessionLifecycleService:
    """Manage authoritative room phases and durable participant-visible history."""

    ROOT = "app_data"
    TERMINAL_PHASES = {"completed", "abandoned"}

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

    @staticmethod
    def _participant(room: dict[str, Any], uid: str) -> dict[str, Any] | None:
        return (room.get("participants") or {}).get(uid)

    @staticmethod
    def _actor_name(room: dict[str, Any], uid: str) -> str:
        participant = LiveCookSessionLifecycleService._participant(room, uid) or {}
        return str(participant.get("display_name") or "Cook")[:80]

    def _event(
        self,
        room_ref: Any,
        room: dict[str, Any],
        *,
        event_type: str,
        actor_uid: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event_id = uuid.uuid4().hex
        record = {
            "id": event_id,
            "correlation_id": event_id,
            "session_id": str(room.get("session_id") or room.get("id") or ""),
            "recipe_id": str((room.get("recipe") or {}).get("id") or ""),
            "type": event_type,
            "message": message,
            "actor_uid": actor_uid,
            "actor_name": self._actor_name(room, actor_uid),
            "payload": payload or {},
            "created_at": self._now(),
        }
        room_ref.child("activity").child(event_id).set(record)
        return record

    def initialize_waiting(self, enterprise_id: str, room_id: str) -> None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get() or {}
        state = room.get("state") or {}
        state.update(
            {
                "session_status": "waiting",
                "started_at": None,
                "completed_at": None,
                "completed_by": None,
                "abandoned_at": None,
                "abandoned_by": None,
                "started_by": None,
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
        if current == target and target in self.TERMINAL_PHASES:
            return room
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
            self._event(
                room_ref,
                room,
                event_type="cooking_session_started",
                actor_uid=actor_uid,
                message=f"{self._actor_name(room, actor_uid)} started cooking.",
            )
        elif target in self.TERMINAL_PHASES:
            if current != "active":
                raise ValueError("Only an active cooking session can be finished")
            now = self._now()
            timestamp_key = "completed_at" if target == "completed" else "abandoned_at"
            actor_key = "completed_by" if target == "completed" else "abandoned_by"
            state.update(
                {
                    "session_status": target,
                    timestamp_key: now,
                    actor_key: actor_uid,
                    "revision": int(state.get("revision") or 0) + 1,
                    "updated_at": now,
                    "updated_by": actor_uid,
                }
            )
            room_ref.child("state").set(state)
            room_ref.update({"updated_at": now, "status": target})
            verb = "completed" if target == "completed" else "ended early"
            self._event(
                room_ref,
                room,
                event_type=f"cooking_session_{target}",
                actor_uid=actor_uid,
                message=f"{self._actor_name(room, actor_uid)} {verb} the cooking session.",
                payload={"final_revision": state["revision"]},
            )
        else:
            raise ValueError("Unsupported cooking session phase")

        return room_ref.get()

    def history(
        self,
        enterprise_id: str,
        room_id: str,
        actor_uid: str,
    ) -> dict[str, Any] | None:
        room = self._room(enterprise_id, room_id).get()
        if not room:
            return None
        if not self._participant(room, actor_uid):
            raise PermissionError("Only session participants can view this cooking history")
        activity = sorted(
            (room.get("activity") or {}).values(),
            key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")),
        )
        feedback = room.get("feedback") or {}
        ratings = [
            int(item.get("rating"))
            for item in feedback.values()
            if isinstance(item, dict) and str(item.get("rating") or "").isdigit()
        ]
        recipe = room.get("recipe") or {}
        state = room.get("state") or {}
        return {
            "room_id": room_id,
            "session_id": str(room.get("session_id") or room_id),
            "title": str(room.get("title") or recipe.get("title") or "Cooking session"),
            "recipe": {
                "id": recipe.get("id"),
                "title": recipe.get("title") or recipe.get("name"),
                "image_url": recipe.get("image_url") or recipe.get("image"),
            },
            "status": self.phase(room),
            "started_at": state.get("started_at"),
            "ended_at": state.get("completed_at") or state.get("abandoned_at"),
            "participants": [
                {
                    "uid": item.get("uid"),
                    "display_name": item.get("display_name"),
                    "role": item.get("role"),
                }
                for item in (room.get("participants") or {}).values()
            ],
            "events": activity,
            "feedback_summary": {
                "count": len(feedback),
                "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "would_cook_again": sum(
                    1
                    for item in feedback.values()
                    if isinstance(item, dict) and item.get("would_cook_again") is True
                ),
            },
            "my_feedback": feedback.get(actor_uid),
            "recording": {"enabled": False, "provider": None, "replay_url": None},
        }

    def record_feedback(
        self,
        enterprise_id: str,
        room_id: str,
        actor_uid: str,
        *,
        rating: int,
        would_cook_again: bool,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        if not room:
            return None
        if not self._participant(room, actor_uid):
            raise PermissionError("Only session participants can leave feedback")
        if self.phase(room) not in self.TERMINAL_PHASES:
            raise ValueError("Feedback is available after the cooking session ends")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        record = {
            "uid": actor_uid,
            "rating": rating,
            "would_cook_again": bool(would_cook_again),
            "note": " ".join(str(note or "").split())[:500],
            "updated_at": self._now(),
        }
        room_ref.child("feedback").child(actor_uid).set(record)
        self._event(
            room_ref,
            room,
            event_type="post_cook_feedback_recorded",
            actor_uid=actor_uid,
            message=f"{self._actor_name(room, actor_uid)} shared post-cook feedback.",
            payload={"rating": rating, "would_cook_again": bool(would_cook_again)},
        )
        return record
