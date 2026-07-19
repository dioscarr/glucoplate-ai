from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db
from livekit import api

from app.services.firebase_auth_service import FirebaseAuthService


class LiveCookMediaService:
    """Authorize and persist optional media state beside the cooking room."""

    ROOT = "app_data"

    def __init__(self) -> None:
        self.app = FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _device_id(value: str | None) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_-]", "", str(value or ""))[:80]
        return cleaned or "default"

    def _room(self, enterprise_id: str, room_id: str):
        return db.reference(
            f"{self.ROOT}/enterprises/{enterprise_id}/live_cook_rooms/{room_id}",
            app=self.app,
        )

    def access(self, enterprise_id: str, room_id: str, uid: str, device_id: str | None = None, device_label: str | None = None) -> dict[str, Any] | None:
        room = self._room(enterprise_id, room_id).get()
        participants = (room or {}).get("participants") or {}
        if not room or uid not in participants:
            return None
        phase = str((room.get("state") or {}).get("session_status") or "waiting")
        if room.get("status") == "completed" or phase == "completed":
            raise ValueError("Media is unavailable after the cooking session is completed")
        provider = str(os.getenv("LIVE_COOK_MEDIA_PROVIDER", "browser")).strip().lower() or "browser"
        participant = participants.get(uid) or {}
        display_name = participant.get("display_name") or "Cook"
        safe_device_id = self._device_id(device_id)
        safe_device_label = " ".join(str(device_label or "Device").strip().split())[:40] or "Device"
        media_name = f"{display_name} · {safe_device_label}"
        access: dict[str, Any] = {
            "room_id": room_id,
            "provider": provider,
            "mode": "local-preview",
            "remote_enabled": False,
            "participant": {
                "uid": uid,
                "role": participant.get("role") or "participant",
                "display_name": display_name,
                "device_id": safe_device_id,
                "device_label": safe_device_label,
            },
            "recording": {"enabled": False, "consent_required": True},
            "fallback": "The synchronized cooking room remains available without media.",
        }
        if provider == "livekit":
            server_url = str(os.getenv("LIVEKIT_URL", "")).strip()
            api_key = str(os.getenv("LIVEKIT_API_KEY", "")).strip()
            api_secret = str(os.getenv("LIVEKIT_API_SECRET", "")).strip()
            if not all((server_url, api_key, api_secret)):
                access["configuration_error"] = "LiveKit credentials are incomplete"
                return access
            livekit_room = f"glucoplate-{enterprise_id}-{room_id}"
            identity = f"{enterprise_id}:{uid}:{safe_device_id}"
            token = (
                api.AccessToken(api_key, api_secret)
                .with_identity(identity)
                .with_name(media_name)
                .with_metadata(
                    json.dumps(
                        {
                            "glucoplate_uid": uid,
                            "enterprise_id": enterprise_id,
                            "room_id": room_id,
                            "device_id": safe_device_id,
                            "device_label": safe_device_label,
                        }
                    )
                )
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=livekit_room,
                        can_publish=True,
                        can_subscribe=True,
                        can_publish_data=False,
                    )
                )
                .to_jwt()
            )
            access.update(
                {
                    "mode": "provider",
                    "remote_enabled": True,
                    "serverUrl": server_url,
                    "participantToken": token,
                    "server_url": server_url,
                    "token": token,
                    "livekit_room": livekit_room,
                }
            )
        return access

    def update_state(
        self,
        enterprise_id: str,
        room_id: str,
        uid: str,
        state: dict[str, Any],
        device_id: str | None = None,
        device_label: str | None = None,
    ) -> dict[str, Any] | None:
        safe_device_id = self._device_id(device_id)
        access = self.access(enterprise_id, room_id, uid, safe_device_id, device_label)
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
            "device_id": safe_device_id,
            "device_label": access["participant"]["device_label"],
            "provider": access["provider"],
            "updated_at": self._now(),
        }
        self._room(enterprise_id, room_id).child("media").child("participants").child(uid).child(safe_device_id).set(record)
        return record
