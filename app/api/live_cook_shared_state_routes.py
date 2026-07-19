from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.firebase_live_cook_room_service import FirebaseLiveCookRoomService
from app.services.live_cook_shared_state_service import LiveCookSharedStateService

router = APIRouter(prefix="/api/live-cook-rooms", tags=["live-cook-shared-state"])


class IngredientStatePayload(BaseModel):
    ingredient_index: int | None = Field(default=None, ge=0, le=1000)
    ingredient_id: str | None = Field(default=None, min_length=1, max_length=120)
    checked: bool
    expected_revision: int | None = Field(default=None, ge=0)


class ServingsStatePayload(BaseModel):
    servings: int = Field(ge=1, le=12)
    expected_revision: int | None = Field(default=None, ge=0)


class TimerStatePayload(BaseModel):
    action: Literal["start", "pause", "resume", "reset"]
    duration_seconds: int | None = Field(default=None, ge=1, le=86400)
    expected_revision: int | None = Field(default=None, ge=0)


def shared_state() -> LiveCookSharedStateService:
    try:
        return LiveCookSharedStateService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


def room_service() -> FirebaseLiveCookRoomService:
    try:
        return FirebaseLiveCookRoomService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Firebase Realtime Database is unavailable") from exc


def _room_response(raw: dict[str, Any], enterprise_id: str, room_id: str) -> dict[str, Any]:
    room = room_service().get_room(enterprise_id, room_id)
    return {"ok": True, "room": room or raw}


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, (ValueError, IndexError)):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Shared cooking state could not be updated")


@router.put("/{room_id}/ingredients")
def set_shared_ingredient(
    room_id: str,
    payload: IngredientStatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        raw = shared_state().set_ingredient(
            user.enterprise_id,
            room_id,
            user.uid,
            payload.ingredient_index,
            payload.ingredient_id,
            payload.checked,
            payload.expected_revision,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _room_response(raw, user.enterprise_id, room_id)


@router.put("/{room_id}/servings")
def update_shared_servings(
    room_id: str,
    payload: ServingsStatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        raw = shared_state().set_servings(
            user.enterprise_id,
            room_id,
            user.uid,
            payload.servings,
            payload.expected_revision,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _room_response(raw, user.enterprise_id, room_id)


@router.post("/{room_id}/timer")
def update_shared_timer(
    room_id: str,
    payload: TimerStatePayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        raw = shared_state().update_timer(
            user.enterprise_id,
            room_id,
            user.uid,
            payload.action,
            payload.duration_seconds,
            payload.expected_revision,
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _room_response(raw, user.enterprise_id, room_id)
