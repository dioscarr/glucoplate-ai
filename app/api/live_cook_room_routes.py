from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_live_cook_room_service import FirebaseLiveCookRoomService

router = APIRouter(prefix="/api/live-cook-rooms", tags=["live-cook-rooms"])


class CreateRoomPayload(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    display_name: str | None = Field(default=None, max_length=80)
    visibility: Literal["private", "public"] = "private"
    recipe: dict[str, Any] = Field(default_factory=dict)


class JoinRoomPayload(BaseModel):
    invite_code: str = Field(min_length=4, max_length=12)
    display_name: str | None = Field(default=None, max_length=80)

    @field_validator("invite_code", mode="before")
    @classmethod
    def normalize_invite_code(cls, value: Any) -> str:
        normalized = "".join(character for character in str(value or "").upper() if character.isalnum())
        if not normalized:
            raise ValueError("Invite code is required")
        return normalized


class JoinActiveRoomPayload(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)


class ReadyPayload(BaseModel):
    ready: bool


class RoomStatePayload(BaseModel):
    current_step: int | None = Field(default=None, ge=0, le=1000)
    ingredient_checks: dict[str, bool] | None = None
    timer: dict[str, Any] | None = None


class ChatPayload(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    kind: Literal["message", "reaction", "help"] = "message"


class InsightPayload(BaseModel):
    provider: Literal["auto", "gemini", "groq", "local"] = "auto"


def service() -> FirebaseLiveCookRoomService:
    try:
        return FirebaseLiveCookRoomService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


def require_participant(room: dict[str, Any], uid: str) -> None:
    if uid not in {str(item.get("uid")) for item in room.get("participants") or []}:
        raise HTTPException(status_code=403, detail="Join the room before accessing it")


@router.post("", status_code=201)
def create_room(
    payload: CreateRoomPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().create_room(user.enterprise_id, user.uid, payload.model_dump())
    return {"ok": True, "room": room}


@router.post("/join")
def join_room(
    payload: JoinRoomPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().join_room(
        user.enterprise_id,
        user.uid,
        payload.invite_code,
        payload.display_name,
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Active cook room not found")
    return {"ok": True, "room": room}


@router.get("/active")
def list_active_rooms(
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    rooms = service().list_active_rooms(user.enterprise_id)
    return {"rooms": rooms, "count": len(rooms)}


@router.post("/join/{room_id}")
def join_active_room(
    room_id: str,
    payload: JoinActiveRoomPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().join_room_by_id(
        user.enterprise_id,
        user.uid,
        room_id,
        payload.display_name,
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Active cook room not found")
    return {"ok": True, "room": room}


@router.get("/activity/public")
def public_activity(
    user: Annotated[AuthContext, Depends(scoped_user)],
    limit: int = Query(default=30, ge=1, le=100),
) -> dict[str, Any]:
    items = service().public_activity(user.enterprise_id, limit)
    return {"items": items, "count": len(items)}


@router.get("/{room_id}")
def get_room(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().get_room(user.enterprise_id, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Cook room not found")
    require_participant(room, user.uid)
    return {"room": room}


@router.put("/{room_id}/ready")
def set_ready(
    room_id: str,
    payload: ReadyPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().set_ready(user.enterprise_id, room_id, user.uid, payload.ready)
    if room is None:
        raise HTTPException(status_code=404, detail="Cook room participant not found")
    return {"ok": True, "room": room}


@router.post("/{room_id}/presence")
def heartbeat(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().heartbeat(user.enterprise_id, room_id, user.uid)
    if room is None:
        raise HTTPException(status_code=404, detail="Cook room participant not found")
    require_participant(room, user.uid)
    return {"ok": True, "room": room}


@router.patch("/{room_id}/state")
def update_room_state(
    room_id: str,
    payload: RoomStatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No room state changes supplied")
    room_api = service()
    current = room_api.get_room(user.enterprise_id, room_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Cook room not found")
    require_participant(current, user.uid)
    phase = str((current.get("state") or {}).get("session_status") or "waiting")
    if phase != "active":
        raise HTTPException(status_code=409, detail="Shared cooking state can only change while the session is active")
    if "ingredient_checks" in updates or "timer" in updates:
        raise HTTPException(status_code=409, detail="Use the shared ingredient and timer endpoints for conflict-safe updates")
    room = room_api.update_state(user.enterprise_id, room_id, user.uid, updates)
    if room is None:
        raise HTTPException(status_code=404, detail="Cook room participant not found")
    return {"ok": True, "room": room}


@router.post("/{room_id}/chat", status_code=201)
def add_chat(
    room_id: str,
    payload: ChatPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    item = service().add_chat(
        user.enterprise_id,
        room_id,
        user.uid,
        payload.message,
        payload.kind,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cook room participant not found")
    return {"ok": True, "item": item}


@router.post("/{room_id}/insights")
def generate_room_insights(
    room_id: str,
    payload: InsightPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    room = service().get_room(user.enterprise_id, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Cook room not found")
    require_participant(room, user.uid)
    from app.services.live_cook_insight_service import LiveCookInsightService

    return {"ok": True, "insight": LiveCookInsightService().generate(room, payload.provider)}


@router.delete("/{room_id}/participants/me")
def leave_room(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, bool]:
    if not service().leave_room(user.enterprise_id, room_id, user.uid):
        raise HTTPException(status_code=404, detail="Cook room participant not found")
    return {"ok": True}
