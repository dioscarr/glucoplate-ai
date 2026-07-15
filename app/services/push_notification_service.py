from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

_STORE_LOCK = Lock()
_FIREBASE_LOCK = Lock()


class PushNotificationService:
    def __init__(self) -> None:
        self.store_path = Path(os.getenv("GLUCOPLATE_PUSH_STORE", "data/push_tokens.json"))

    @property
    def firebase_config(self) -> dict[str, str]:
        return {
            "apiKey": os.getenv("FIREBASE_WEB_API_KEY", ""),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("FIREBASE_APP_ID", ""),
        }

    @property
    def vapid_public_key(self) -> str:
        return os.getenv("FIREBASE_VAPID_PUBLIC_KEY", "")

    def client_configured(self) -> bool:
        required = ("apiKey", "projectId", "messagingSenderId", "appId")
        return bool(self.vapid_public_key and all(self.firebase_config.get(key) for key in required))

    def server_configured(self) -> bool:
        return bool(
            os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )

    def configured(self) -> bool:
        return self.client_configured() and self.server_configured()

    def _read(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        try:
            value = json.loads(self.store_path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, values: list[dict[str, Any]]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(values, indent=2), encoding="utf-8")

    def save_token(
        self,
        token: str,
        user_id: str | None = None,
        profile_id: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        token = token.strip()
        if not token:
            raise ValueError("Firebase messaging token is required")
        record = {
            "token": token,
            "provider": "firebase",
            "user_id": user_id,
            "profile_id": profile_id,
            "device_name": device_name,
            "enabled": True,
        }
        with _STORE_LOCK:
            values = self._read()
            existing = next((item for item in values if item.get("token") == token), None)
            if existing:
                existing.update(record)
                record = existing
            else:
                values.append(record)
            self._write(values)
        return record

    def remove_token(self, token: str) -> bool:
        with _STORE_LOCK:
            values = self._read()
            remaining = [item for item in values if item.get("token") != token]
            changed = len(remaining) != len(values)
            if changed:
                self._write(remaining)
            return changed

    def token_registered(self, token: str) -> bool:
        return any(
            item.get("enabled") and item.get("token") == token
            for item in self._read()
        )

    def _firebase_app(self):
        import firebase_admin
        from firebase_admin import credentials

        try:
            return firebase_admin.get_app()
        except ValueError:
            pass

        with _FIREBASE_LOCK:
            try:
                return firebase_admin.get_app()
            except ValueError:
                service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                if service_account_json:
                    credential = credentials.Certificate(json.loads(service_account_json))
                    return firebase_admin.initialize_app(credential)
                return firebase_admin.initialize_app()

    def _send_token(self, token: str, payload: dict[str, Any]) -> bool:
        from firebase_admin import messaging

        title = str(payload.get("title") or "GlucoPlate AI")
        body = str(payload.get("body") or "Your kitchen update is ready.")
        url = str(payload.get("url") or "/static/index.html")
        tag = str(payload.get("tag") or "glucoplate-update")
        message = messaging.Message(
            token=token,
            data={"title": title, "body": body, "url": url, "tag": tag},
            webpush=messaging.WebpushConfig(
                headers={"Urgency": "normal"},
                fcm_options=messaging.WebpushFCMOptions(link=url),
            ),
        )
        messaging.send(message)
        return True

    def send_to_registered_token(self, token: str, payload: dict[str, Any]) -> dict[str, int | bool]:
        if not self.server_configured():
            return {"configured": False, "registered": False, "sent": 0, "failed": 0}
        if not self.token_registered(token):
            return {"configured": True, "registered": False, "sent": 0, "failed": 0}

        from firebase_admin import messaging

        self._firebase_app()
        try:
            self._send_token(token, payload)
            return {"configured": True, "registered": True, "sent": 1, "failed": 0}
        except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
            self.remove_token(token)
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}
        except Exception:
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}

    def send(self, payload: dict[str, Any], user_id: str | None = None) -> dict[str, int | bool]:
        if not self.server_configured():
            return {"configured": False, "sent": 0, "failed": 0}

        from firebase_admin import messaging

        self._firebase_app()
        records = [item for item in self._read() if item.get("enabled") and item.get("token")]
        if user_id:
            records = [item for item in records if item.get("user_id") == user_id]

        sent = failed = 0
        invalid_tokens: set[str] = set()

        for record in records:
            token = str(record["token"])
            try:
                self._send_token(token, payload)
                sent += 1
            except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
                failed += 1
                invalid_tokens.add(token)
            except Exception:
                failed += 1

        if invalid_tokens:
            with _STORE_LOCK:
                values = [item for item in self._read() if item.get("token") not in invalid_tokens]
                self._write(values)

        return {"configured": True, "sent": sent, "failed": failed}
