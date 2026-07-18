from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger

_STORE_LOCK = Lock()
_FIREBASE_LOCK = Lock()


class PushNotificationService:
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
                    profile_id TEXT,
                    device_name TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            count = connection.execute("SELECT COUNT(*) FROM push_tokens").fetchone()[0]
            if count == 0 and self.legacy_store_path.exists():
                try:
                    values = json.loads(self.legacy_store_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    values = []
                for item in values if isinstance(values, list) else []:
                    token = str(item.get("token") or "").strip()
                    if token:
                        connection.execute(
                            "INSERT OR REPLACE INTO push_tokens (token, provider, user_id, profile_id, device_name, enabled) VALUES (?, ?, ?, ?, ?, ?)",
                            (token, "firebase", item.get("user_id"), item.get("profile_id"), item.get("device_name"), int(bool(item.get("enabled", True)))),
                        )

    def _read(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM push_tokens ORDER BY updated_at DESC")]

    def save_token(self, token: str, user_id: str | None = None, profile_id: str | None = None, device_name: str | None = None) -> dict[str, Any]:
        token = token.strip()
        if not token:
            raise ValueError("Firebase messaging token is required")
        if not user_id:
            raise ValueError("Authenticated Firebase user is required")
        with _STORE_LOCK, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO push_tokens (token, provider, user_id, profile_id, device_name, enabled)
                VALUES (?, 'firebase', ?, ?, ?, 1)
                ON CONFLICT(token) DO UPDATE SET
                    user_id=excluded.user_id,
                    profile_id=excluded.profile_id,
                    device_name=excluded.device_name,
                    enabled=1,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (token, user_id, profile_id, device_name),
            )
            row = connection.execute("SELECT * FROM push_tokens WHERE token = ?", (token,)).fetchone()
        return dict(row)

    def remove_token(self, token: str, user_id: str | None = None) -> bool:
        if not user_id:
            return False
        with _STORE_LOCK, self._connect() as connection:
            cursor = connection.execute("DELETE FROM push_tokens WHERE token = ? AND user_id = ?", (token, user_id))
            return cursor.rowcount > 0

    def token_registered(self, token: str, user_id: str | None = None) -> bool:
        if not user_id:
            return False
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM push_tokens WHERE token = ? AND user_id = ? AND enabled = 1",
                (token, user_id),
            ).fetchone()
            return row is not None

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

    def _send_token(self, token: str, payload: dict[str, Any]) -> bool:
        from firebase_admin import messaging
        title = str(payload.get("title") or "GlucoPlate AI")
        body = str(payload.get("body") or "Your kitchen update is ready.")
        url = str(payload.get("url") or "/static/index.html")
        tag = str(payload.get("tag") or "glucoplate-update")
        messaging.send(messaging.Message(token=token, data={"title": title, "body": body, "url": url, "tag": tag}, webpush=messaging.WebpushConfig(headers={"Urgency": "normal"})))
        return True

    def send_to_registered_token(self, token: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, int | bool]:
        if not self.server_configured():
            return {"configured": False, "registered": False, "sent": 0, "failed": 0}
        if not self.token_registered(token, user_id=user_id):
            return {"configured": True, "registered": False, "sent": 0, "failed": 0}
        from firebase_admin import messaging
        self._firebase_app()
        try:
            self._send_token(token, payload)
            return {"configured": True, "registered": True, "sent": 1, "failed": 0}
        except messaging.UnregisteredError:
            logger.warning("Firebase test push rejected an unregistered device token")
            self.remove_token(token, user_id=user_id)
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}
        except messaging.SenderIdMismatchError:
            logger.error(
                "Firebase test push sender ID mismatch; verify that the web config, "
                "VAPID key, and service account belong to the same project"
            )
            self.remove_token(token, user_id=user_id)
            return {"configured": True, "registered": True, "sent": 0, "failed": 1}
        except Exception as exc:
            logger.exception(
                "Firebase test push failed with {error_type}: {error}",
                error_type=type(exc).__name__,
                error=str(exc),
            )
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
        for record in records:
            token = str(record["token"])
            try:
                self._send_token(token, payload)
                sent += 1
            except messaging.UnregisteredError:
                failed += 1
                logger.warning("Firebase bulk push rejected an unregistered device token")
                self.remove_token(token, user_id=str(record.get("user_id") or ""))
            except messaging.SenderIdMismatchError:
                failed += 1
                logger.error(
                    "Firebase bulk push sender ID mismatch; verify that all Firebase "
                    "credentials belong to the same project"
                )
                self.remove_token(token, user_id=str(record.get("user_id") or ""))
            except Exception as exc:
                failed += 1
                logger.exception(
                    "Firebase bulk push failed with {error_type}: {error}",
                    error_type=type(exc).__name__,
                    error=str(exc),
                )
        return {"configured": True, "sent": sent, "failed": failed}
