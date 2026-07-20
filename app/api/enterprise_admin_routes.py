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

PERMISSION_REGISTRY = {
    "enterprise.users.read": "View enterprise members",
    "enterprise.users.write": "Change enterprise membership roles and status",
    "enterprise.themes.read": "View enterprise themes",
    "enterprise.themes.write": "Create, update, activate, and delete enterprise themes",
    "enterprise.roles.read": "View custom enterprise roles",
    "enterprise.roles.write": "Create custom enterprise roles",
    "platform.enterprises.read": "View enterprises across the platform",
    "platform.enterprises.write": "Create enterprises and access codes",
}
BUILTIN_ROLE_PERMISSIONS = {
    "platform_admin": set(PERMISSION_REGISTRY),
    "enterprise_owner": {permission for permission in PERMISSION_REGISTRY if permission.startswith("enterprise.")},
    "enterprise_admin": {permission for permission in PERMISSION_REGISTRY if permission.startswith("enterprise.")},
    "admin": {permission for permission in PERMISSION_REGISTRY if permission.startswith("enterprise.")},
}


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


class EnterpriseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    plan: str = Field(default="starter", max_length=40)


class AccessCodeCreate(BaseModel):
    label: str | None = Field(default=None, max_length=160)


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    permissions: list[str] = Field(default_factory=list, max_length=100)
    visibility: list[str] = Field(default_factory=list, max_length=100)


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


def resolved_authorization_profile(user: AuthContext) -> dict[str, Any]:
    configured = (
        directory().authorization_profile(user.enterprise_id, user.role)
        if user.enterprise_id
        else {"role": user.role, "permissions": [], "visibility": []}
    )
    configured_permissions = set(configured.get("permissions") or [])
    permissions = sorted(configured_permissions | BUILTIN_ROLE_PERMISSIONS.get(user.role, set()))
    return {
        **configured,
        "role": user.role,
        "permissions": permissions,
        "visibility": sorted(set(configured.get("visibility") or [])),
        "permission_registry": PERMISSION_REGISTRY,
    }


def require_permission(permission: str):
    if permission not in PERMISSION_REGISTRY:
        raise ValueError(f"Unknown permission: {permission}")

    def dependency(user: Annotated[AuthContext, Depends(current_user)]) -> AuthContext:
        if permission not in resolved_authorization_profile(user)["permissions"]:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        if permission.startswith("enterprise.") and not user.enterprise_id:
            raise HTTPException(status_code=403, detail="Enterprise membership is required")
        return user

    return dependency


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
def list_enterprise_users(user: Annotated[AuthContext, Depends(require_permission("enterprise.users.read"))]) -> dict:
    enterprise_id = _enterprise_id(user)
    return {"enterprise_id": enterprise_id, "users": directory().list_members(enterprise_id)}


@router.patch("/admin/users/{user_id}")
def update_enterprise_user(user_id: str, update: MemberUpdate, actor: Annotated[AuthContext, Depends(require_permission("enterprise.users.write"))]) -> dict:
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
def list_enterprise_themes(user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.read"))]) -> dict:
    return themes().list(_enterprise_id(user))


@router.post("/admin/themes")
def create_enterprise_theme(request: ThemeCreate, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))]) -> dict:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Theme name is required")
    theme = themes().create(_enterprise_id(user), name=request.name, source_theme_id=request.source_theme_id)
    _audit_theme(user, "theme.created", theme)
    return {"ok": True, "theme": theme}


@router.get("/admin/themes/{theme_id}")
def get_enterprise_theme_by_id(theme_id: str, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.read"))]) -> dict:
    return {"theme": themes().get(_enterprise_id(user), theme_id)}


@router.put("/admin/themes/{theme_id}")
def save_enterprise_theme_by_id(theme_id: str, update: ThemeUpdate, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))], publish: bool = False) -> dict:
    saved = themes().save(_enterprise_id(user), update.model_dump(exclude_none=True), theme_id=theme_id, publish=publish)
    _audit_theme(user, "theme.published" if publish else "theme.saved", saved)
    return {"ok": True, "theme": saved}


@router.post("/admin/themes/{theme_id}/activate")
def activate_enterprise_theme(theme_id: str, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))]) -> dict:
    try:
        theme = themes().activate(_enterprise_id(user), theme_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_theme(user, "theme.activated", theme)
    return {"ok": True, "theme": theme}


@router.delete("/admin/themes/{theme_id}")
def delete_enterprise_theme(theme_id: str, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))]) -> dict:
    try:
        active = themes().delete(_enterprise_id(user), theme_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "theme": active}


# Backwards-compatible endpoints used by the existing Theme Studio.
@router.get("/admin/theme")
def get_enterprise_theme(user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.read"))]) -> dict:
    return {"theme": themes().get(_enterprise_id(user))}


@router.put("/admin/theme")
def save_enterprise_theme(update: ThemeUpdate, user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))], publish: bool = False) -> dict:
    saved = themes().save(_enterprise_id(user), update.model_dump(exclude_none=True), theme_id=update.id, publish=publish)
    _audit_theme(user, "theme.published" if publish else "theme.saved", saved)
    return {"ok": True, "theme": saved}


@router.delete("/admin/theme")
def reset_enterprise_theme(user: Annotated[AuthContext, Depends(require_permission("enterprise.themes.write"))], theme_id: str | None = None) -> dict:
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
def list_enterprises(user: Annotated[AuthContext, Depends(require_permission("platform.enterprises.read"))]) -> dict:
    return {"enterprises": directory().list_enterprises()}

@router.post("/platform/enterprises")
def create_platform_enterprise(request: EnterpriseCreate, user: Annotated[AuthContext, Depends(require_permission("platform.enterprises.write"))]) -> dict:
    name = request.name.strip()
    slug = (request.slug or name.lower().replace(" ", "-")).strip("-")
    try:
        enterprise = directory().create_enterprise(name=name, slug=slug, plan=request.plan.strip() or "starter")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    directory().record_audit(enterprise_id=enterprise["id"], actor_uid=user.uid, action="enterprise.created", target_type="enterprise", target_id=enterprise["id"], details_json=json.dumps({"name": enterprise["name"], "slug": enterprise["slug"], "plan": enterprise["plan"]}, sort_keys=True))
    return {"ok": True, "enterprise": enterprise}

@router.post("/platform/enterprises/{enterprise_id}/access-codes")
def create_platform_access_code(enterprise_id: str, request: AccessCodeCreate, user: Annotated[AuthContext, Depends(require_permission("platform.enterprises.write"))]) -> dict:
    try:
        code = directory().create_access_code(enterprise_id, label=request.label.strip() if request.label else None)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    directory().record_audit(enterprise_id=enterprise_id, actor_uid=user.uid, action="access_code.created", target_type="enterprise_access_code", target_id=code["id"], details_json=json.dumps({"label": code.get("label")}, sort_keys=True))
    return {"ok": True, "access_code": code}

@router.get("/platform/enterprises/{enterprise_id}/access-codes")
def list_platform_access_codes(enterprise_id: str, user: Annotated[AuthContext, Depends(require_permission("platform.enterprises.read"))]) -> dict:
    return {"enterprise_id": enterprise_id, "access_codes": directory().list_access_codes(enterprise_id)}
@router.post("/admin/roles")
def create_role(request: RoleCreate, user: Annotated[AuthContext, Depends(require_permission("enterprise.roles.write"))]) -> dict:
    enterprise_id = _enterprise_id(user)
    try:
        role = directory().create_role(enterprise_id, name=request.name.strip(), permissions=request.permissions, visibility=request.visibility)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    directory().record_audit(enterprise_id=enterprise_id, actor_uid=user.uid, action="role.created", target_type="enterprise_role", target_id=role["id"], details_json=json.dumps({"name": role["name"], "permissions": role["permissions"], "visibility": role["visibility"]}, sort_keys=True))
    return {"ok": True, "role": role}

@router.get("/admin/roles")
def list_roles(user: Annotated[AuthContext, Depends(require_permission("enterprise.roles.read"))]) -> dict:
    return {"enterprise_id": _enterprise_id(user), "roles": directory().list_roles(_enterprise_id(user))}

@router.get("/authorization/profile")
def authorization_profile(user: Annotated[AuthContext, Depends(current_user)]) -> dict:
    if not user.enterprise_id:
        return {"role": user.role, "permissions": [], "visibility": []}
    return resolved_authorization_profile(user)