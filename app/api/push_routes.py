import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.push_notification_service import PushNotificationService

router = APIRouter(prefix="/api/push", tags=["push"])


class TokenRequest(BaseModel):
    token: str = Field(min_length=20)
    user_id: str | None = None
    profile_id: str | None = None
    device_name: str | None = None


class UnsubscribeRequest(BaseModel):
    token: str = Field(min_length=20)


class PushMessageRequest(BaseModel):
    title: str = Field(default="GlucoPlate AI", max_length=80)
    body: str = Field(default="Your kitchen update is ready.", max_length=240)
    url: str = "/static/index.html"
    tag: str = "glucoplate-update"
    user_id: str | None = None


@router.get("/config")
def push_config() -> dict:
    service = PushNotificationService()
    return {
        "supported": True,
        "provider": "firebase",
        "configured": service.configured(),
        "client_configured": service.client_configured(),
        "server_configured": service.server_configured(),
        "firebase_config": service.firebase_config,
        "vapid_public_key": service.vapid_public_key,
    }


@router.post("/tokens")
def save_token(request: TokenRequest) -> dict:
    try:
        record = PushNotificationService().save_token(
            request.token,
            user_id=request.user_id,
            profile_id=request.profile_id,
            device_name=request.device_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "subscription": record}


@router.delete("/tokens")
def remove_token(request: UnsubscribeRequest) -> dict:
    return {"ok": PushNotificationService().remove_token(request.token)}


@router.post("/send")
def send_push(
    request: PushMessageRequest,
    x_push_admin_key: str | None = Header(default=None),
) -> dict:
    expected_key = os.getenv("PUSH_ADMIN_KEY", "")
    if not expected_key or x_push_admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Push administrator key is required")

    result = PushNotificationService().send(
        {
            "title": request.title,
            "body": request.body,
            "url": request.url,
            "tag": request.tag,
        },
        user_id=request.user_id,
    )
    return {"ok": bool(result.get("configured")), **result}