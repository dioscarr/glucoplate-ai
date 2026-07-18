from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_live_cook_room_service import FirebaseLiveCookRoomService
from app.services.live_cook_session_lifecycle_service import LiveCookSessionLifecycleService

router = APIRouter(prefix="/api/live-cook-rooms", tags=["live-cook-room-lifecycle"])


def lifecycle() -> LiveCookSessionLifecycleService:
    try:
        return LiveCookSessionLifecycleService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


def room_service() -> FirebaseLiveCookRoomService:
    try:
        return FirebaseLiveCookRoomService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


def transition_room(
    room_id: str,
    target: Literal["active", "completed"],
    user: AuthContext,
) -> dict[str, Any]:
    try:
        raw = lifecycle().transition(user.enterprise_id, room_id, user.uid, target)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if raw is None:
        raise HTTPException(status_code=404, detail="Cook room not found")
    room = room_service().get_room(user.enterprise_id, room_id)
    return {"ok": True, "room": room or raw}


@router.post("/{room_id}/start")
def start_cooking(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    return transition_room(room_id, "active", user)


@router.post("/{room_id}/complete")
def complete_cooking(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    return transition_room(room_id, "completed", user)
