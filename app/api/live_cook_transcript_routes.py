from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.enterprise_admin_routes import AuthContext
from app.api.user_data_routes import scoped_user
from app.services.live_cook_transcript_service import LiveCookTranscriptService


router = APIRouter(prefix="/api/live-cook-rooms", tags=["live-cook-transcript"])


class TranscriptConsentPayload(BaseModel):
    accepted: bool
    enable_room: bool | None = None


class TranscriptSegmentPayload(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    started_at: str | None = Field(default=None, max_length=80)
    ended_at: str | None = Field(default=None, max_length=80)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provider: Literal["browser", "livekit", "groq", "openai", "other"] = "browser"


def service() -> LiveCookTranscriptService:
    try:
        return LiveCookTranscriptService()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Live transcript state is unavailable") from exc


@router.get("/{room_id}/transcription")
def get_transcription(
    room_id: str,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    state = service().get(user.enterprise_id, room_id, user.uid)
    if state is None:
        raise HTTPException(status_code=403, detail="Join the room before viewing its transcript")
    return {"transcription": state}


@router.put("/{room_id}/transcription/consent")
def set_transcription_consent(
    room_id: str,
    payload: TranscriptConsentPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        state = service().set_consent(
            user.enterprise_id,
            room_id,
            user.uid,
            accepted=payload.accepted,
            enable_room=payload.enable_room,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if state is None:
        raise HTTPException(status_code=403, detail="Join the room before changing transcription")
    return {"ok": True, "transcription": state}


@router.post("/{room_id}/transcription/segments", status_code=201)
def add_transcript_segment(
    room_id: str,
    payload: TranscriptSegmentPayload,
    user: Annotated[AuthContext, Depends(scoped_user)],
) -> dict[str, Any]:
    try:
        segment = service().add_segment(
            user.enterprise_id,
            room_id,
            user.uid,
            payload.model_dump(),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if segment is None:
        raise HTTPException(status_code=403, detail="Join the room before adding transcript text")
    return {"ok": True, "segment": segment}
