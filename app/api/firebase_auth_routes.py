from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from firebase_admin import auth
from pydantic import BaseModel, Field

from app.services.enterprise_auth_service import EnterpriseAuthService
from app.services.firebase_auth_service import FirebaseAuthService

router = APIRouter(prefix="/api/firebase-auth", tags=["firebase-auth"])


class EnterpriseEnrollmentRequest(BaseModel):
    access_code: str = Field(min_length=1, max_length=64)


def _verified_user(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Firebase bearer token is required")

    token = authorization.split(" ", 1)[1].strip()
    try:
        return FirebaseAuthService().verify_id_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as exc:
        raise HTTPException(status_code=401, detail="Firebase ID token is invalid or expired") from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Firebase authentication failed") from exc


@router.get("/config")
def firebase_auth_config() -> dict:
    service = FirebaseAuthService()
    return {
        "provider": "firebase",
        "client_configured": service.client_configured(),
        "server_configured": service.server_configured(),
        "firebase_config": service.client_config,
    }


@router.post("/enterprise/enroll")
def enterprise_enroll(
    request: EnterpriseEnrollmentRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    user = _verified_user(authorization)
    company = EnterpriseAuthService().validate_access_code(request.access_code)
    if not company:
        raise HTTPException(status_code=403, detail="The company access code is invalid or inactive")

    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Firebase user identifier is missing")

    claims = {
        "company_id": company["id"],
        "company_name": company["name"],
        "role": company["role"],
        "enterprise": True,
    }
    FirebaseAuthService().set_custom_user_claims(uid, claims)
    return {"ok": True, "company": company, "refresh_token": True}


def _sync_enterprise_directory(user: dict, claims: dict) -> dict | None:
    company_id = claims.get("company_id") or claims.get("enterprise_id")
    if not company_id:
        return None

    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Firebase user identifier is missing")

    # Import lazily to avoid coupling router initialization while still using the
    # same cached directory instance as the enterprise admin endpoints.
    from app.api.enterprise_admin_routes import directory

    try:
        return directory().upsert_authenticated_user(
            firebase_uid=uid,
            email=user.get("email"),
            display_name=user.get("name"),
            enterprise_id=company_id,
            role=claims.get("role") or "member",
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/session")
def firebase_session(authorization: str | None = Header(default=None)) -> dict:
    user = _verified_user(authorization)
    claims = user.pop("claims", {})
    company_id = claims.get("company_id") or claims.get("enterprise_id")
    enterprise = None
    membership = None
    if company_id:
        membership = _sync_enterprise_directory(user, claims)
        enterprise = {
            "company_id": company_id,
            "company_name": claims.get("company_name") or claims.get("enterprise_name"),
            "role": claims.get("role", "member"),
        }
    return {"ok": True, "user": user, "enterprise": enterprise, "membership": membership}
