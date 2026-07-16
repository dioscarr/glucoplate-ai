from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.services.enterprise_directory import EnterpriseDirectory
from app.services.firebase_auth_service import FirebaseAuthService
from app.services.firebase_realtime_enterprise_directory import FirebaseRealtimeEnterpriseDirectory

router = APIRouter(prefix="/api/enterprise", tags=["enterprise-admin"])

ADMIN_ROLES = {"platform_admin", "enterprise_owner", "enterprise_admin", "admin"}
PLATFORM_ROLES = {"platform_admin"}
ALLOWED_ROLES = {"enterprise_owner", "enterprise_admin", "manager", "member", "viewer"}


class AuthContext(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None
    enterprise_id: str | None = None
    enterprise_name: str | None = None
    role: str = "member"


class MemberUpdate(BaseModel):
    role: Literal["enterprise_owner", "enterprise_admin", "manager", "member", "viewer"] | None = None
    status: Literal["active", "disabled"] | None = None


@lru_cache(maxsize=1)
def directory() -> Any:
    firebase = FirebaseAuthService()
    if firebase.realtime_database_configured():
        service = FirebaseRealtimeEnterpriseDirectory()
    else:
        service = EnterpriseDirectory()
    service.create_schema()
    service.seed_enterprise(
        enterprise_id="glucoplate",
        name="GlucoPlate AI",
        slug="glucoplate",
        plan="enterprise",
    )
    return service


def current_user(authorization: Annotated[str | None, Header()] = None) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Firebase bearer token is required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        verified = FirebaseAuthService().verify_id_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Firebase authentication failed") from exc

    claims = verified.get("claims") or {}
    uid = verified.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Firebase token does not contain a user id")
    return AuthContext(
        uid=uid,
        email=verified.get("email"),
        name=verified.get("name"),
        enterprise_id=claims.get("company_id") or claims.get("enterprise_id"),
        enterprise_name=claims.get("company_name") or claims.get("enterprise_name"),
        role=claims.get("role") or "member",
    )


def require_enterprise_admin(user: Annotated[AuthContext, Depends(current_user)]) -> AuthContext:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Enterprise administrator permission is required")
    if not user.enterprise_id and user.role not in PLATFORM_ROLES:
        raise HTTPException(status_code=403, detail="Enterprise membership is required")
    return user


def require_platform_admin(user: Annotated[AuthContext, Depends(current_user)]) -> AuthContext:
    if user.role not in PLATFORM_ROLES:
        raise HTTPException(status_code=403, detail="Platform administrator permission is required")
    return user


@router.post("/session")
def sync_enterprise_session(user: Annotated[AuthContext, Depends(current_user)]) -> dict:
    if not user.enterprise_id:
        raise HTTPException(status_code=403, detail="User is not assigned to an enterprise")
    try:
        membership = directory().upsert_authenticated_user(
            firebase_uid=user.uid,
            email=user.email,
            display_name=user.name,
            enterprise_id=user.enterprise_id,
            role=user.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"ok": True, "membership": membership}


@router.get("/admin/users")
def list_enterprise_users(user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    if not user.enterprise_id:
        raise HTTPException(status_code=400, detail="Select an enterprise before listing users")
    return {"enterprise_id": user.enterprise_id, "users": directory().list_members(user.enterprise_id)}


@router.patch("/admin/users/{user_id}")
def update_enterprise_user(
    user_id: str,
    update: MemberUpdate,
    actor: Annotated[AuthContext, Depends(require_enterprise_admin)],
) -> dict:
    if not actor.enterprise_id:
        raise HTTPException(status_code=400, detail="Select an enterprise before updating users")
    if update.role and update.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported enterprise role")
    try:
        membership = directory().update_member(
            actor.enterprise_id,
            user_id,
            role=update.role,
            status=update.status,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    directory().record_audit(
        enterprise_id=actor.enterprise_id,
        actor_uid=actor.uid,
        action="membership.updated",
        target_type="enterprise_user",
        target_id=user_id,
        details_json=json.dumps(update.model_dump(exclude_none=True), sort_keys=True),
    )
    return {"ok": True, "membership": membership}


@router.get("/platform/enterprises")
def list_enterprises(user: Annotated[AuthContext, Depends(require_platform_admin)]) -> dict:
    return {"enterprises": directory().list_enterprises()}
