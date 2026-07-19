from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookSharedStateService:
    """Mutate shared cooking state only while the authoritative session is active."""

    ROOT = "app_data"

    def __init__(self) -> None:
        firebase = FirebaseAuthService()
        self.app = firebase._firebase_app()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.astimezone(UTC).isoformat()

    @staticmethod
    def _phase(room: dict[str, Any]) -> str:
        return str((room.get("state") or {}).get("session_status") or "waiting")

    def _room(self, enterprise_id: str, room_id: str):
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_rooms/{room_id}",
            app=self.app,
        )

    def _load_active_participant(
        self, enterprise_id: str, room_id: str, uid: str
    ) -> tuple[Any, dict[str, Any], dict[str, Any]]:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        if not room:
            raise LookupError("Cook room not found")
        participant = (room.get("participants") or {}).get(uid)
        if not participant:
            raise PermissionError("Join the room before changing shared cooking state")
        phase = self._phase(room)
        if phase != "active":
            raise ValueError(
                "Shared cooking state can only change while the session is active"
            )
        return room_ref, room, participant

    @staticmethod
    def _assert_revision(state: dict[str, Any], expected_revision: int | None) -> None:
        if expected_revision is None:
            return
        actual = int(state.get("revision") or 0)
        if actual != expected_revision:
            raise RuntimeError(
                f"Room state changed from revision {expected_revision} to {actual}; refresh and try again"
            )

    def _activity(
        self,
        room_ref: Any,
        event_type: str,
        message: str,
        uid: str,
        display_name: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        activity_id = uuid.uuid4().hex
        room_ref.child("activity").child(activity_id).set(
            {
                "id": activity_id,
                "type": event_type,
                "message": message,
                "actor_uid": uid,
                "actor_name": display_name,
                "payload": payload or {},
                "created_at": self._iso(self._now()),
            }
        )

    def set_ingredient(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        ingredient_index: int,
        checked: bool,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        room_ref, room, participant = self._load_active_participant(
            enterprise_id, room_id, uid
        )
        ingredients = (room.get("recipe") or {}).get("ingredients") or []
        if ingredient_index < 0 or ingredient_index >= len(ingredients):
            raise IndexError("Ingredient does not exist in this recipe")
        state = room.get("state") or {}
        self._assert_revision(state, expected_revision)
        checks = dict(state.get("ingredient_checks") or {})
        checks[str(ingredient_index)] = bool(checked)
        now = self._iso(self._now())
        state.update(
            {
                "ingredient_checks": checks,
                "revision": int(state.get("revision") or 0) + 1,
                "updated_at": now,
                "updated_by": uid,
            }
        )
        room_ref.child("state").set(state)
        room_ref.update({"updated_at": now})
        name = str(participant.get("display_name") or "Cook")
        ingredient = ingredients[ingredient_index]
        label = ingredient.get("name") if isinstance(ingredient, dict) else str(ingredient)
        self._activity(
            room_ref,
            "ingredient_checked" if checked else "ingredient_unchecked",
            f"{name} {'checked' if checked else 'unchecked'} {label or 'an ingredient'}.",
            uid,
            name,
            {"ingredient_index": ingredient_index, "checked": bool(checked)},
        )
        return room_ref.get() or room

    def set_servings(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        servings: int,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        room_ref, room, participant = self._load_active_participant(
            enterprise_id, room_id, uid
        )
        if str(room.get("host_uid") or "") != str(uid):
            raise PermissionError("Only the Chef can change servings for the room")
        if servings < 1 or servings > 12:
            raise ValueError("Servings must be between 1 and 12")
        state = room.get("state") or {}
        self._assert_revision(state, expected_revision)
        now = self._iso(self._now())
        state.update(
            {
                "selected_servings": servings,
                "revision": int(state.get("revision") or 0) + 1,
                "updated_at": now,
                "updated_by": uid,
            }
        )
        recipe = dict(room.get("recipe") or {})
        recipe["selected_servings"] = servings
        room_ref.child("state").set(state)
        room_ref.child("recipe").set(recipe)
        room_ref.update({"updated_at": now})
        name = str(participant.get("display_name") or "Chef")
        self._activity(
            room_ref,
            "servings_changed",
            f"{name} set the room recipe to {servings} serving{'s' if servings != 1 else ''}.",
            uid,
            name,
            {"selected_servings": servings},
        )
        return room_ref.get() or room

    def update_timer(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        action: Literal["start", "pause", "resume", "reset"],
        duration_seconds: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        room_ref, room, participant = self._load_active_participant(
            enterprise_id, room_id, uid
        )
        state = room.get("state") or {}
        self._assert_revision(state, expected_revision)
        timer = dict(state.get("timer") or {})
        now_dt = self._now()
        now = self._iso(now_dt)

        if action == "start":
            if duration_seconds is None or duration_seconds < 1 or duration_seconds > 86400:
                raise ValueError("Timer duration must be between 1 second and 24 hours")
            timer = {
                "status": "running",
                "duration_seconds": duration_seconds,
                "remaining_seconds": duration_seconds,
                "started_at": now,
                "ends_at": self._iso(now_dt + timedelta(seconds=duration_seconds)),
                "paused_at": None,
                "updated_at": now,
                "updated_by": uid,
            }
        elif action == "pause":
            if timer.get("status") != "running" or not timer.get("ends_at"):
                raise ValueError("Only a running timer can be paused")
            ends_at = datetime.fromisoformat(str(timer["ends_at"]).replace("Z", "+00:00"))
            remaining = max(0, int((ends_at - now_dt).total_seconds()))
            timer.update(
                {
                    "status": "completed" if remaining == 0 else "paused",
                    "remaining_seconds": remaining,
                    "paused_at": now,
                    "ends_at": None,
                    "updated_at": now,
                    "updated_by": uid,
                }
            )
        elif action == "resume":
            if timer.get("status") != "paused":
                raise ValueError("Only a paused timer can be resumed")
            remaining = int(timer.get("remaining_seconds") or 0)
            if remaining < 1:
                raise ValueError("The timer has already finished")
            timer.update(
                {
                    "status": "running",
                    "started_at": now,
                    "ends_at": self._iso(now_dt + timedelta(seconds=remaining)),
                    "paused_at": None,
                    "updated_at": now,
                    "updated_by": uid,
                }
            )
        elif action == "reset":
            timer = {
                "status": "idle",
                "duration_seconds": 0,
                "remaining_seconds": 0,
                "started_at": None,
                "ends_at": None,
                "paused_at": None,
                "updated_at": now,
                "updated_by": uid,
            }
        else:
            raise ValueError("Unsupported timer action")

        state.update(
            {
                "timer": timer,
                "revision": int(state.get("revision") or 0) + 1,
                "updated_at": now,
                "updated_by": uid,
            }
        )
        room_ref.child("state").set(state)
        room_ref.update({"updated_at": now})
        name = str(participant.get("display_name") or "Cook")
        self._activity(
            room_ref,
            f"timer_{action}",
            f"{name} {action}{'ed' if action != 'pause' else 'd'} the shared timer.",
            uid,
            name,
            {"action": action, "timer": timer},
        )
        return room_ref.get() or room
