from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger

_STORE_LOCK = Lock()
_FIREBASE_LOCK = Lock()


class PushNotificationService:
    """Store web-push subscriptions durably and deliver Firebase messages."""

    def __init__(self) -> None:
        self.db_path = Path(os.getenv("GLUCOPLATE_PUSH_DB", "data/push_tokens.db"))
        self.legacy_store_path = Path(os.getenv("GLUCOPLATE_PUSH_STORE", "data/push_tokens.json"))
        self._initialize_store()

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
        return bool(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    def configured(self) -> bool:
        return self.client_configured() and self.server_configured()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _token_key(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_store(self) -> None:
        with _STORE_LOCK, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS push_tokens (
                    token TEXT PRIMARY KEY,
                    provider TEXT NOT NULL DEFAULT 'firebase',
                    user_id TEXT,
                    enterprise_id TEXT,
                    profile_id TEXT,
                    device_name TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(push_tokens)")}
            if "enterprise_id" not in columns:
                connection.execute("ALTER TABLE push_tokens ADD COLUMN enterprise_id TEXT")

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
                value = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
                return firebase_admin.initialize_app(credentials.Certificate(json.loads(value))) if value else firebase_admin.initialize_app()

    def _remote_tokens(self, enterprise_id: str):
        from firebase_admin import db

        return db.reference(
            f"app_data/enterprises/{enterprise_id}/push_tokens",
            app=self._firebase_app(),
        )

    def _read(self, enterprise_id: str | None = None) -> list[dict[str, Any]]:
        if enterprise_id and self.server_configured():
            values = self._remote_tokens(enterprise_id).get() or {}
            return [item for item in values.values() if isinstance(item, dict)]
        with self._connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM push_tokens ORDER BY updated_at DESC")]

    def save_token(
        self,
        token: str,
        user_id: str | None = None,
        enterprise_id: str | None = None,
        profile_id: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        token = token.strip()
        if not token:
            raise ValueError("Firebase messaging token is required")
        if not user_id:
            raise ValueError("Authenticated Firebase user is required")
        if not enterprise_id:
            raise ValueError("Enterprise membership is required")
        record = {
            "token": token,
            "provider": "firebase",
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "profile_id": profile_id,
            "device_name": device_name,
            "enabled": True,
            "updated_at": self._now(),
        }
        with _STORE_LOCK, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO push_tokens (token, provider, user_id, enterprise_id, profile_id, device_name, enabled)
                VALUES (?, 'firebase', ?, ?, ?, ?, 1)
                ON CONFLICT(token) DO UPDATE SET
                    user_id=excluded.user_id,
                    enterprise_id=excluded.enterprise_id,
                    profile_id=excluded.profile_id,
                    device_name=excluded.device_name,
                    enabled=1,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (token, user_id, enterprise_id, profile_id, device_name),
            )
        if self.server_configured():
            self._remote_tokens(enterprise_id).child(self._token_key(token)).set(record)
        return record

    def remove_token(
        self,
        token: str,
        user_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> bool:
        if not user_id:
            return False
        removed = False
        with _STORE_LOCK, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM push_tokens WHERE token = ? AND user_id = ?",
                (token, user_id),
            )
            removed = cursor.rowcount > 0
        if enterprise_id and self.server_configured():
            ref = self._remote_tokens(enterprise_id).child(self._token_key(token))
            remote = ref.get()
            if remote and str(remote.get("user_id")) == str(user_id):
                ref.delete()
                removed = True
        return removed

    def token_registered(
        self,
        token: str,
        user_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> bool:
        if not user_id:
            return False
        return any(
            item.get("token") == token
            and str(item.get("user_id")) == str(user_id)
            and bool(item.get("enabled"))
            for item in self._read(enterprise_id)
        )

    def _send_token(self, token: str, payload: dict[str, Any]) -> bool:
        from firebase_admin import messaging

        messaging.send(
            messaging.Message(
                token=token,
                data={
                    "title": str(payload.get("title") or "GlucoPlate AI"),
                    "body": str(payload.get("body") or "Your kitchen update is ready."),
                    "url": str(payload.get("url") or "/static/index.html"),
                    "tag": str(payload.get("tag") or "glucoplate-update"),
                },
                webpush=messaging.WebpushConfig(headers={"Urgency": "high"}),
            )
        )
        return True

    def send_to_registered_token(
        self,
        token: str,
        payload: dict[str, Any],
        user_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> dict[str, int | bool]:
        if not self.server_configured():
            return {"configured": False, "registered": False, "sent": 0, "failed": 0}
        if not self.token_registered(token, user_id=user_id, enterprise_id=enterprise_id):
            return {"configured": True, "registered": False, "sent": 0, "failed": 0}
        from firebase_admin import messaging

        self._firebase_app()
        try:
            self._send_token(token, payload)
            return {"configured": True, "registered": True, "sent": 1, "failed": 0}
        except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
            self.remove_token(token, user_id=user_id, enterprise_id=enterprise_id)
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}
        except Exception as exc:
            logger.exception("Firebase test push failed: {error}", error=str(exc))
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}

    def send(
        self,
        payload: dict[str, Any],
        user_id: str | None = None,
        enterprise_id: str | None = None,
    ) -> dict[str, int | bool]:
        if not self.server_configured():
            return {"configured": False, "matched": 0, "sent": 0, "failed": 0}
        from firebase_admin import messaging

        self._firebase_app()
        records = [item for item in self._read(enterprise_id) if item.get("enabled") and item.get("token")]
        if user_id:
            records = [item for item in records if item.get("user_id") == user_id]
        if enterprise_id:
            records = [item for item in records if item.get("enterprise_id") == enterprise_id]
        sent = failed = 0
        for record in records:
            token = str(record["token"])
            try:
                self._send_token(token, payload)
                sent += 1
            except (messaging.UnregisteredError, messaging.SenderIdMismatchError):
                failed += 1
                self.remove_token(
                    token,
                    user_id=str(record.get("user_id") or ""),
                    enterprise_id=enterprise_id or str(record.get("enterprise_id") or ""),
                )
            except Exception as exc:
                failed += 1
                logger.exception("Firebase bulk push failed: {error}", error=str(exc))
        return {"configured": True, "matched": len(records), "sent": sent, "failed": failed}
