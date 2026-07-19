from __future__ import annotations

import secrets
import string
import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebaseLiveCookRoomService:
    """Persist collaborative cooking rooms in Firebase Realtime Database."""

    ROOT = "app_data"
    CODE_LENGTH = 6

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _clean_name(value: str | None, fallback: str = "Cook") -> str:
        cleaned = " ".join(str(value or "").strip().split())
        return cleaned[:80] or fallback

    @staticmethod
    def _servings(recipe: dict[str, Any]) -> int:
        try:
            return self._servings(recipe)
        except (TypeError, ValueError):
            return 4

    def _rooms(self, enterprise_id: str):
        return db.reference(f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_rooms")

    def _codes(self, enterprise_id: str):
        return db.reference(f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_room_codes")

    def _room(self, enterprise_id: str, room_id: str):
        return self._rooms(enterprise_id).child(room_id)

    def _new_code(self, enterprise_id: str) -> str:
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(20):
            code = "".join(secrets.choice(alphabet) for _ in range(self.CODE_LENGTH))
            if self._codes(enterprise_id).child(code).get() is None:
                return code
        raise RuntimeError("Could not allocate an invite code")

    def _activity(
        self,
        enterprise_id: str,
        room_id: str,
        *,
        event_type: str,
        message: str,
        actor_uid: str | None = None,
        actor_name: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        activity_id = uuid.uuid4().hex
        record = {
            "id": activity_id,
            "type": event_type,
            "message": message,
            "actor_uid": actor_uid,
            "actor_name": actor_name,
            "payload": payload or {},
            "created_at": self._now(),
        }
        self._room(enterprise_id, room_id).child("activity").child(activity_id).set(record)
        return record

    def create_room(
        self,
        enterprise_id: str,
        uid: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        room_id = uuid.uuid4().hex
        code = self._new_code(enterprise_id)
        now = self._now()
        host_name = self._clean_name(payload.get("display_name"), "Host")
        recipe = payload.get("recipe") or {}
        ingredients = recipe.get("ingredients") or []
        participant = {
            "uid": uid,
            "display_name": host_name,
            "role": "host",
            "ready": True,
            "online": True,
            "joined_at": now,
            "last_seen_at": now,
        }
        room = {
            "id": room_id,
            "invite_code": code,
            "title": self._clean_name(payload.get("title"), recipe.get("title") or "Live Cook Room"),
            "visibility": payload.get("visibility") or "private",
            "status": "active",
            "host_uid": uid,
            "recipe": recipe,
            "state": {
                "current_step": 0,
                "selected_servings": max(1, min(12, int(recipe.get("selected_servings") or recipe.get("base_servings") or recipe.get("servings") or 4))),
                "ingredient_checks": {str(index): False for index, _ in enumerate(ingredients)},
                "timer": None,
                "revision": 1,
                "updated_at": now,
                "updated_by": uid,
            },
            "participants": {uid: participant},
            "created_at": now,
            "updated_at": now,
        }
        self._room(enterprise_id, room_id).set(room)
        self._codes(enterprise_id).child(code).set(room_id)
        self._activity(
            enterprise_id,
            room_id,
            event_type="room_created",
            message=f"{host_name} started the cook room.",
            actor_uid=uid,
            actor_name=host_name,
        )
        return self.get_room(enterprise_id, room_id) or room

    def find_by_code(self, enterprise_id: str, code: str) -> str | None:
        normalized = str(code or "").strip().upper()
        return self._codes(enterprise_id).child(normalized).get()

    def list_active_rooms(self, enterprise_id: str) -> list[dict[str, Any]]:
        rooms = (self._rooms(enterprise_id).get() or {}).values()
        items: list[dict[str, Any]] = []
        for room in rooms:
            phase = str((room.get("state") or {}).get("session_status") or "waiting")
            if room.get("status") != "active" or phase == "completed":
                continue
            participants = list((room.get("participants") or {}).values())
            host = next(
                (item for item in participants if str(item.get("uid")) == str(room.get("host_uid"))),
                {},
            )
            items.append(
                {
                    "id": room.get("id"),
                    "title": room.get("title") or "Live Cook Room",
                    "host_name": host.get("display_name") or "Host",
                    "participant_count": len(participants),
                    "session_status": phase,
                    "current_step": int((room.get("state") or {}).get("current_step") or 0),
                    "updated_at": room.get("updated_at"),
                }
            )
        return sorted(items, key=lambda item: str(item.get("updated_at") or ""), reverse=True)

    def join_room_by_id(
        self,
        enterprise_id: str,
        uid: str,
        room_id: str,
        display_name: str | None,
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        phase = str((room.get("state") or {}).get("session_status") or "waiting") if room else "completed"
        if not room or room.get("status") != "active" or phase == "completed":
            return None
        now = self._now()
        name = self._clean_name(display_name, "Guest")
        existing = (room.get("participants") or {}).get(uid) or {}
        participant = {
            **existing,
            "uid": uid,
            "display_name": name,
            "role": existing.get("role") or "participant",
            "ready": bool(existing.get("ready", False)),
            "online": True,
            "joined_at": existing.get("joined_at") or now,
            "last_seen_at": now,
        }
        room_ref.child("participants").child(uid).set(participant)
        room_ref.update({"updated_at": now})
        if not existing:
            self._activity(
                enterprise_id,
                room_id,
                event_type="participant_joined",
                message=f"{name} joined the room.",
                actor_uid=uid,
                actor_name=name,
            )
        return self.get_room(enterprise_id, room_id)

    def join_room(
        self,
        enterprise_id: str,
        uid: str,
        code: str,
        display_name: str | None,
    ) -> dict[str, Any] | None:
        room_id = self.find_by_code(enterprise_id, code)
        if not room_id:
            return None
        return self.join_room_by_id(enterprise_id, uid, room_id, display_name)

    def get_room(self, enterprise_id: str, room_id: str) -> dict[str, Any] | None:
        room = self._room(enterprise_id, room_id).get()
        if not room:
            return None
        room["participants"] = list((room.get("participants") or {}).values())
        room["chat"] = sorted(
            (room.get("chat") or {}).values(),
            key=lambda item: str(item.get("created_at") or ""),
        )[-100:]
        room["activity"] = sorted(
            (room.get("activity") or {}).values(),
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )[:100]
        return room

    def set_ready(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        ready: bool,
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        participant = room_ref.child("participants").child(uid).get()
        if participant is None:
            return None
        participant.update({"ready": ready, "online": True, "last_seen_at": self._now()})
        room_ref.child("participants").child(uid).set(participant)
        name = self._clean_name(participant.get("display_name"), "Cook")
        self._activity(
            enterprise_id,
            room_id,
            event_type="participant_ready",
            message=f"{name} is {'ready' if ready else 'not ready'}.",
            actor_uid=uid,
            actor_name=name,
            payload={"ready": ready},
        )
        return self.get_room(enterprise_id, room_id)

    def update_state(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        if not room or uid not in (room.get("participants") or {}):
            return None
        state = room.get("state") or {}
        allowed = {key: value for key, value in updates.items() if key in {"current_step", "ingredient_checks", "timer"}}
        state.update(allowed)
        state["revision"] = int(state.get("revision") or 0) + 1
        state["updated_at"] = self._now()
        state["updated_by"] = uid
        room_ref.child("state").set(state)
        room_ref.update({"updated_at": state["updated_at"]})
        participant = (room.get("participants") or {}).get(uid) or {}
        name = self._clean_name(participant.get("display_name"), "Cook")
        if "current_step" in allowed:
            step_number = int(allowed["current_step"]) + 1
            self._activity(
                enterprise_id,
                room_id,
                event_type="step_changed",
                message=f"{name} moved everyone to step {step_number}.",
                actor_uid=uid,
                actor_name=name,
                payload={"current_step": allowed["current_step"]},
            )
        return self.get_room(enterprise_id, room_id)

    def add_chat(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        message: str,
        kind: str = "message",
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        participant = (room.get("participants") or {}).get(uid) if room else None
        if not participant:
            return None
        chat_id = uuid.uuid4().hex
        record = {
            "id": chat_id,
            "uid": uid,
            "display_name": self._clean_name(participant.get("display_name"), "Cook"),
            "message": " ".join(message.strip().split())[:1000],
            "kind": kind,
            "created_at": self._now(),
        }
        room_ref.child("chat").child(chat_id).set(record)
        if kind == "help":
            self._activity(
                enterprise_id,
                room_id,
                event_type="help_requested",
                message=f"{record['display_name']} needs help.",
                actor_uid=uid,
                actor_name=record["display_name"],
            )
        return record

    def leave_room(self, enterprise_id: str, room_id: str, uid: str) -> bool:
        room_ref = self._room(enterprise_id, room_id)
        participant_ref = room_ref.child("participants").child(uid)
        participant = participant_ref.get()
        if participant is None:
            return False
        participant.update({"online": False, "ready": False, "last_seen_at": self._now()})
        participant_ref.set(participant)
        name = self._clean_name(participant.get("display_name"), "Cook")
        self._activity(
            enterprise_id,
            room_id,
            event_type="participant_left",
            message=f"{name} left the room.",
            actor_uid=uid,
            actor_name=name,
        )
        return True

    def public_activity(self, enterprise_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rooms = (self._rooms(enterprise_id).get() or {}).values()
        items: list[dict[str, Any]] = []
        for room in rooms:
            if room.get("visibility") != "public":
                continue
            room_title = room.get("title") or "Live Cook Room"
            for activity in (room.get("activity") or {}).values():
                items.append({**activity, "room_id": room.get("id"), "room_title": room_title})
        return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)[:limit]
