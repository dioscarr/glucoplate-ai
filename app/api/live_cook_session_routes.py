from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_live_cook_room_service import FirebaseLiveCookRoomService
from app.services.live_cook_session_lifecycle_service import LiveCookSessionLifecycleService
from app.services.push_notification_service import PushNotificationService

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


def notify_enterprise_session_started(enterprise_id: str, room: dict[str, Any]) -> None:
    try:
        title = str(room.get("title") or "Live Cook Room")
        host = next(
            (
                str(item.get("display_name") or "A cook")
                for item in room.get("participants") or []
                if str(item.get("uid")) == str(room.get("host_uid"))
            ),
            "A cook",
        )
        invite_code = str(room.get("invite_code") or "")
        result = PushNotificationService().send(
            {
                "title": "Live cooking started",
                "body": f"{host} started {title}. Join with code {invite_code}.",
                "url": f"/static/index.html?live_room={room.get('id')}",
                "tag": f"live-cook-started-{room.get('id')}",
            },
            enterprise_id=enterprise_id,
        )
        logger.info(
            "Live cooking organization push finished: enterprise={enterprise_id} room={room_id} sent={sent} failed={failed}",
            enterprise_id=enterprise_id,
            room_id=room.get("id"),
            sent=result.get("sent", 0),
            failed=result.get("failed", 0),
        )
    except Exception as exc:
        logger.exception(
            "Live cooking organization push failed after room start: {error}",
            error=str(exc),
        )


@router.post("/{room_id}/start")
def start_cooking(
    room_id: str,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    result = transition_room(room_id, "active", user)
    background_tasks.add_task(
        notify_enterprise_session_started,
        user.enterprise_id,
        result["room"],
    )
    return result


@router.post("/{room_id}/complete")
def complete_cooking(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    return transition_room(room_id, "completed", user)
