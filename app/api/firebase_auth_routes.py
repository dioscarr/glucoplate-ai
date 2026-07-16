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


@router.get("/session")
def firebase_session(authorization: str | None = Header(default=None)) -> dict:
    user = _verified_user(authorization)
    claims = user.pop("claims", {})
    company_id = claims.get("company_id")
    enterprise = None
    if company_id:
        enterprise = {
            "company_id": company_id,
            "company_name": claims.get("company_name"),
            "role": claims.get("role", "member"),
        }
    return {"ok": True, "user": user, "enterprise": enterprise}
