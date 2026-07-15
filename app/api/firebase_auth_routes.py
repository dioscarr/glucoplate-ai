from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from firebase_admin import auth

from app.services.firebase_auth_service import FirebaseAuthService

router = APIRouter(prefix="/api/firebase-auth", tags=["firebase-auth"])


@router.get("/config")
def firebase_auth_config() -> dict:
    service = FirebaseAuthService()
    return {
        "provider": "firebase",
        "client_configured": service.client_configured(),
        "server_configured": service.server_configured(),
        "firebase_config": service.client_config,
    }


@router.get("/session")
def firebase_session(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Firebase bearer token is required")

    token = authorization.split(" ", 1)[1].strip()
    try:
        user = FirebaseAuthService().verify_id_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as exc:
        raise HTTPException(status_code=401, detail="Firebase ID token is invalid or expired") from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Firebase authentication failed") from exc

    return {"ok": True, "user": {key: value for key, value in user.items() if key != "claims"}}
