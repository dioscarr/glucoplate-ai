from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any

_FIREBASE_AUTH_LOCK = Lock()


class FirebaseAuthService:
    @property
    def client_config(self) -> dict[str, str]:
        return {
            "apiKey": os.getenv("FIREBASE_WEB_API_KEY", ""),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("FIREBASE_APP_ID", ""),
            "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", ""),
        }

    def client_configured(self) -> bool:
        required = ("apiKey", "authDomain", "projectId", "appId")
        return all(self.client_config.get(key) for key in required)

    def server_configured(self) -> bool:
        return bool(
            os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )

    def _firebase_app(self):
        import firebase_admin
        from firebase_admin import credentials

        try:
            return firebase_admin.get_app()
        except ValueError:
            pass

        with _FIREBASE_AUTH_LOCK:
            try:
                return firebase_admin.get_app()
            except ValueError:
                service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if service_account_json:
                    credential = credentials.Certificate(json.loads(service_account_json))
                    return firebase_admin.initialize_app(credential)
                return firebase_admin.initialize_app()

    def verify_id_token(self, token: str) -> dict[str, Any]:
        if not self.server_configured():
            raise RuntimeError("Firebase server credentials are not configured")
        if not token.strip():
            raise ValueError("Firebase ID token is required")

        from firebase_admin import auth

        self._firebase_app()
        claims = auth.verify_id_token(token, check_revoked=True)
        return {
            "uid": claims.get("uid") or claims.get("sub"),
            "email": claims.get("email"),
            "name": claims.get("name"),
            "picture": claims.get("picture"),
            "email_verified": bool(claims.get("email_verified")),
            "provider": (claims.get("firebase") or {}).get("sign_in_provider"),
            "claims": claims,
        }
