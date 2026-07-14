from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

_STORE_LOCK = Lock()


class PushNotificationService:
    def __init__(self) -> None:
        self.store_path = Path(os.getenv("GLUCOPLATE_PUSH_STORE", "data/push_subscriptions.json"))

    @property
    def vapid_public_key(self) -> str:
        return os.getenv("VAPID_PUBLIC_KEY", "")

    @property
    def vapid_private_key(self) -> str:
        return os.getenv("VAPID_PRIVATE_KEY", "")

    @property
    def vapid_subject(self) -> str:
        return os.getenv("VAPID_SUBJECT", "mailto:admin@glucoplate.app")

    def configured(self) -> bool:
        return bool(self.vapid_public_key and self.vapid_private_key)

    def _read(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, values: list[dict[str, Any]]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(values, indent=2), encoding="utf-8")

    def save(self, subscription: dict[str, Any], user_id: str | None = None, profile_id: str | None = None) -> dict[str, Any]:
        endpoint = subscription.get("endpoint")
        if not endpoint:
            raise ValueError("Push subscription endpoint is required")
        with _STORE_LOCK:
            values = self._read()
            record = {"subscription": subscription, "user_id": user_id, "profile_id": profile_id}
            existing = next((item for item in values if item.get("subscription", {}).get("endpoint") == endpoint), None)
            if existing:
                existing.update(record)
            else:
                values.append(record)
            self._write(values)
        return record

    def remove(self, endpoint: str) -> bool:
        with _STORE_LOCK:
            values = self._read()
            remaining = [item for item in values if item.get("subscription", {}).get("endpoint") != endpoint]
            changed = len(remaining) != len(values)
            if changed:
                self._write(remaining)
            return changed

    def send(self, payload: dict[str, Any], user_id: str | None = None) -> dict[str, int | bool]:
        if not self.configured():
            return {"configured": False, "sent": 0, "failed": 0}
        from pywebpush import WebPushException, webpush

        records = self._read()
        if user_id:
            records = [item for item in records if item.get("user_id") == user_id]
        sent = failed = 0
        for record in records:
            try:
                webpush(
                    subscription_info=record["subscription"],
                    data=json.dumps(payload),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims={"sub": self.vapid_subject},
                )
                sent += 1
            except WebPushException:
                failed += 1
        return {"configured": True, "sent": sent, "failed": failed}
