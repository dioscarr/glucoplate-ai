from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookTranscriptService:
    """Persist consent state and finalized speech transcript segments per room."""

    ROOT = "app_data"
    MAX_SEGMENTS = 500

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

    @staticmethod
    def _participant(room: dict[str, Any] | None, uid: str) -> dict[str, Any] | None:
        return ((room or {}).get("participants") or {}).get(uid)

    def get(self, enterprise_id: str, room_id: str, uid: str) -> dict[str, Any] | None:
        room = self._room(enterprise_id, room_id).get()
        if not room or not self._participant(room, uid):
            return None
        state = room.get("transcription") or {}
        segments = sorted(
            (state.get("segments") or {}).values(),
            key=lambda item: str(item.get("started_at") or item.get("created_at") or ""),
        )[-self.MAX_SEGMENTS :]
        consents = state.get("consents") or {}
        return {
            "enabled": bool(state.get("enabled")),
            "enabled_at": state.get("enabled_at"),
            "enabled_by": state.get("enabled_by"),
            "raw_audio_retained": False,
            "consented": bool(consents.get(uid, {}).get("accepted")),
            "participant_consents": {
                key: bool(value.get("accepted")) for key, value in consents.items()
            },
            "segments": segments,
            "segment_count": len(segments),
        }

    def set_consent(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        *,
        accepted: bool,
        enable_room: bool | None = None,
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        participant = self._participant(room, uid)
        if not room or not participant:
            return None
        phase = str((room.get("state") or {}).get("session_status") or "waiting")
        if phase == "completed" or room.get("status") == "completed":
            raise ValueError("Transcription is unavailable after the session ends")
        transcription_ref = room_ref.child("transcription")
        now = self._now()
        if enable_room is not None:
            if str(room.get("host_uid") or "") != uid:
                raise PermissionError("Only the Chef can enable or disable room transcription")
            transcription_ref.update(
                {
                    "enabled": bool(enable_room),
                    "enabled_at": now if enable_room else None,
                    "enabled_by": uid if enable_room else None,
                    "raw_audio_retained": False,
                    "updated_at": now,
                }
            )
        transcription_ref.child("consents").child(uid).set(
            {"accepted": bool(accepted), "updated_at": now}
        )
        return self.get(enterprise_id, room_id, uid)

    def add_segment(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        room_ref = self._room(enterprise_id, room_id)
        room = room_ref.get()
        participant = self._participant(room, uid)
        if not room or not participant:
            return None
        state = room.get("transcription") or {}
        if not state.get("enabled"):
            raise ValueError("Room transcription is not enabled")
        if not ((state.get("consents") or {}).get(uid) or {}).get("accepted"):
            raise PermissionError("Consent is required before submitting transcript text")
        text = " ".join(str(payload.get("text") or "").split())[:2000]
        if not text:
            raise ValueError("Transcript text is required")
        segment_id = uuid.uuid4().hex
        confidence = min(1.0, max(0.0, float(payload.get("confidence") or 0.0)))
        record = {
            "id": segment_id,
            "speaker_uid": uid,
            "speaker_name": str(participant.get("display_name") or "Cook")[:80],
            "started_at": str(payload.get("started_at") or self._now()),
            "ended_at": str(payload.get("ended_at") or self._now()),
            "text": text,
            "status": "final",
            "confidence": confidence,
            "provider": str(payload.get("provider") or "browser")[:40],
            "source": "audio",
            "created_at": self._now(),
        }
        room_ref.child("transcription").child("segments").child(segment_id).set(record)
        room_ref.child("transcription").update({"updated_at": record["created_at"]})
        return record

    def stop(self, enterprise_id: str, room_id: str) -> None:
        self._room(enterprise_id, room_id).child("transcription").update(
            {"enabled": False, "enabled_by": None, "updated_at": self._now()}
        )
