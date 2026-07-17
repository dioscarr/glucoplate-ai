from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.enterprise_directory import EnterpriseDirectory
from app.services.firebase_auth_service import FirebaseAuthService
from app.services.firebase_realtime_enterprise_directory import FirebaseRealtimeEnterpriseDirectory
from app.services.theme_service import ThemeService

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


class ThemeUpdate(BaseModel):
    id: str | None = None
    name: str | None = None
    enabled: bool | None = None
    tokens: dict[str, Any] = Field(default_factory=dict)
    sections: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)
    elements: dict[str, Any] = Field(default_factory=dict)


class ThemeCreate(BaseModel):
    name: str
    source_theme_id: str | None = None


@lru_cache(maxsize=1)
def directory() -> Any:
    firebase = FirebaseAuthService()
    if firebase.realtime_database_configured():
        service = FirebaseRealtimeEnterpriseDirectory()
    else:
        service = EnterpriseDirectory()
    service.create_schema()
    service.seed_enterprise(enterprise_id="glucoplate", name="GlucoPlate AI", slug="glucoplate", plan="enterprise")
    return service


@lru_cache(maxsize=1)
def themes() -> ThemeService:
    return ThemeService()


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
    return AuthContext(uid=uid, email=verified.get("email"), name=verified.get("name"), enterprise_id=claims.get("company_id") or claims.get("enterprise_id"), enterprise_name=claims.get("company_name") or claims.get("enterprise_name"), role=claims.get("role") or "member")


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


def _enterprise_id(user: AuthContext) -> str:
    if not user.enterprise_id:
        raise HTTPException(status_code=400, detail="Select an enterprise before managing themes")
    return user.enterprise_id


def _audit_theme(user: AuthContext, action: str, theme: dict[str, Any]) -> None:
    directory().record_audit(
        enterprise_id=user.enterprise_id,
        actor_uid=user.uid,
        action=action,
        target_type="enterprise_theme",
        target_id=theme.get("id"),
        details_json=json.dumps({"name": theme.get("name"), "version": theme.get("version"), "status": theme.get("status"), "enabled": theme.get("enabled")}),
    )


@router.post("/session")
def sync_enterprise_session(user: Annotated[AuthContext, Depends(current_user)]) -> dict:
    if not user.enterprise_id:
        raise HTTPException(status_code=403, detail="User is not assigned to an enterprise")
    try:
        membership = directory().upsert_authenticated_user(firebase_uid=user.uid, email=user.email, display_name=user.name, enterprise_id=user.enterprise_id, role=user.role)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"ok": True, "membership": membership}


@router.get("/admin/users")
def list_enterprise_users(user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    enterprise_id = _enterprise_id(user)
    return {"enterprise_id": enterprise_id, "users": directory().list_members(enterprise_id)}


@router.patch("/admin/users/{user_id}")
def update_enterprise_user(user_id: str, update: MemberUpdate, actor: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    enterprise_id = _enterprise_id(actor)
    if update.role and update.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported enterprise role")
    try:
        membership = directory().update_member(enterprise_id, user_id, role=update.role, status=update.status)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    directory().record_audit(enterprise_id=enterprise_id, actor_uid=actor.uid, action="membership.updated", target_type="enterprise_user", target_id=user_id, details_json=json.dumps(update.model_dump(exclude_none=True), sort_keys=True))
    return {"ok": True, "membership": membership}


@router.get("/admin/themes")
def list_enterprise_themes(user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    return themes().list(_enterprise_id(user))


@router.post("/admin/themes")
def create_enterprise_theme(request: ThemeCreate, user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Theme name is required")
    theme = themes().create(_enterprise_id(user), name=request.name, source_theme_id=request.source_theme_id)
    _audit_theme(user, "theme.created", theme)
    return {"ok": True, "theme": theme}


@router.get("/admin/themes/{theme_id}")
def get_enterprise_theme_by_id(theme_id: str, user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    return {"theme": themes().get(_enterprise_id(user), theme_id)}


@router.put("/admin/themes/{theme_id}")
def save_enterprise_theme_by_id(theme_id: str, update: ThemeUpdate, user: Annotated[AuthContext, Depends(require_enterprise_admin)], publish: bool = False) -> dict:
    saved = themes().save(_enterprise_id(user), update.model_dump(exclude_none=True), theme_id=theme_id, publish=publish)
    _audit_theme(user, "theme.published" if publish else "theme.saved", saved)
    return {"ok": True, "theme": saved}


@router.post("/admin/themes/{theme_id}/activate")
def activate_enterprise_theme(theme_id: str, user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    try:
        theme = themes().activate(_enterprise_id(user), theme_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_theme(user, "theme.activated", theme)
    return {"ok": True, "theme": theme}


@router.delete("/admin/themes/{theme_id}")
def delete_enterprise_theme(theme_id: str, user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    try:
        active = themes().delete(_enterprise_id(user), theme_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "theme": active}


# Backwards-compatible endpoints used by the existing Theme Studio.
@router.get("/admin/theme")
def get_enterprise_theme(user: Annotated[AuthContext, Depends(require_enterprise_admin)]) -> dict:
    return {"theme": themes().get(_enterprise_id(user))}


@router.put("/admin/theme")
def save_enterprise_theme(update: ThemeUpdate, user: Annotated[AuthContext, Depends(require_enterprise_admin)], publish: bool = False) -> dict:
    saved = themes().save(_enterprise_id(user), update.model_dump(exclude_none=True), theme_id=update.id, publish=publish)
    _audit_theme(user, "theme.published" if publish else "theme.saved", saved)
    return {"ok": True, "theme": saved}


@router.delete("/admin/theme")
def reset_enterprise_theme(user: Annotated[AuthContext, Depends(require_enterprise_admin)], theme_id: str | None = None) -> dict:
    return {"ok": True, "theme": themes().reset(_enterprise_id(user), theme_id)}


@router.get("/themes/{enterprise_id}")
def get_public_themes(enterprise_id: str) -> dict:
    return themes().list(enterprise_id, enabled_only=True)


@router.get("/theme/{enterprise_id}")
def get_public_theme(enterprise_id: str, theme_id: str | None = None) -> dict:
    bundle = themes().list(enterprise_id, enabled_only=True)
    selected_id = theme_id or bundle["activeThemeId"]
    selected = next((item for item in bundle["themes"] if item["id"] == selected_id), None)
    return {"theme": selected or themes().get(enterprise_id)}


@router.get("/platform/enterprises")
def list_enterprises(user: Annotated[AuthContext, Depends(require_platform_admin)]) -> dict:
    return {"enterprises": directory().list_enterprises()}
