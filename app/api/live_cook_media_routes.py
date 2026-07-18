from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.live_cook_media_service import LiveCookMediaService

router = APIRouter(prefix="/api/live-cook-rooms", tags=["live-cook-media"])


class MediaStatePayload(BaseModel):
    camera_enabled: bool | None = None
    microphone_enabled: bool | None = None
    connection_state: Literal["idle", "requesting", "connected", "denied", "unsupported", "failed"] | None = None


def media_service() -> LiveCookMediaService:
    try:
        return LiveCookMediaService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Live media state is unavailable") from exc


@router.get("/{room_id}/media/access")
def media_access(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        access = media_service().access(user.enterprise_id, room_id, user.uid)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if access is None:
        raise HTTPException(status_code=403, detail="Join the cooking room before using media")
    return {"access": access}


@router.put("/{room_id}/media/state")
def update_media_state(
    room_id: str,
    payload: MediaStatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    state = media_service().update_state(
        user.enterprise_id,
        room_id,
        user.uid,
        payload.model_dump(exclude_none=True),
    )
    if state is None:
        raise HTTPException(status_code=403, detail="Join the cooking room before using media")
    return {"ok": True, "media_state": state}
