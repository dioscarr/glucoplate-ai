from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.push_notification_service import PushNotificationService

router = APIRouter(prefix="/api/push", tags=["push"])


class SubscriptionRequest(BaseModel):
    subscription: dict
    user_id: str | None = None
    profile_id: str | None = None


class UnsubscribeRequest(BaseModel):
    endpoint: str


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
        "configured": service.configured(),
        "vapid_public_key": service.vapid_public_key,
    }


@router.post("/subscriptions")
def save_subscription(request: SubscriptionRequest) -> dict:
    try:
        record = PushNotificationService().save(
            request.subscription,
            user_id=request.user_id,
            profile_id=request.profile_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "subscription": record}


@router.delete("/subscriptions")
def remove_subscription(request: UnsubscribeRequest) -> dict:
    return {"ok": PushNotificationService().remove(request.endpoint)}


@router.post("/send")
def send_push(request: PushMessageRequest) -> dict:
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
