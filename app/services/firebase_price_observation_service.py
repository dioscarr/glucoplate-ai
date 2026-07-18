from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


class FirebasePriceObservationService:
    """Store append-only price observations and build recent community summaries."""

    ROOT = "app_data"
    MAX_AGE_DAYS = 90

    def __init__(self) -> None:
        FirebaseAuthService()._firebase_app()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key(value: str | None) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _reporter_hash(uid: str) -> str:
        return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:16]

    def _root(self, enterprise_id: str):
        return db.reference(f"{self.ROOT}/enterprises/{enterprise_id}/price_observations")

    def create_observation(
        self,
        enterprise_id: str,
        uid: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        observation_id = uuid.uuid4().hex
        observed_at = str(payload.get("observed_at") or self._now())
        record = {
            **{key: value for key, value in payload.items() if value is not None},
            "id": observation_id,
            "ingredient_key": self._key(payload.get("ingredient")),
            "store_key": self._key(payload.get("store_name") or payload.get("store_id")),
            "reporter_hash": self._reporter_hash(uid),
            "observed_at": observed_at,
            "created_at": self._now(),
            "reported": False,
        }
        self._root(enterprise_id).child(observation_id).set(record)
        return record

    def report_observation(self, enterprise_id: str, observation_id: str) -> bool:
        ref = self._root(enterprise_id).child(observation_id)
        if ref.get() is None:
            return False
        ref.update({"reported": True, "reported_at": self._now()})
        return True

    def aggregate(
        self,
        enterprise_id: str,
        *,
        ingredient: str | None = None,
        barcode: str | None = None,
        store_name: str | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:
        cutoff = datetime.now(UTC) - timedelta(days=self.MAX_AGE_DAYS)
        ingredient_key = self._key(ingredient)
        store_key = self._key(store_name)
        records = list((self._root(enterprise_id).get() or {}).values())
        matches: list[dict[str, Any]] = []
        for record in records:
            if record.get("reported"):
                continue
            if barcode and str(record.get("barcode") or "") != str(barcode):
                continue
            if ingredient_key and record.get("ingredient_key") != ingredient_key:
                continue
            if store_key and record.get("store_key") != store_key:
                continue
            if currency and str(record.get("currency") or "").upper() != currency.upper():
                continue
            try:
                observed = datetime.fromisoformat(str(record.get("observed_at")))
                if observed.tzinfo is None:
                    observed = observed.replace(tzinfo=UTC)
            except (TypeError, ValueError):
                continue
            if observed < cutoff:
                continue
            if not isinstance(record.get("price"), (int, float)):
                continue
            matches.append(record)

        matches.sort(key=lambda item: str(item.get("observed_at") or ""), reverse=True)
        prices = [float(item["price"]) for item in matches]
        latest = matches[0] if matches else None
        observation_count = len(matches)
        confidence = "high" if observation_count >= 5 else "medium" if observation_count >= 2 else "low" if observation_count else "none"
        return {
            "ingredient": ingredient,
            "barcode": barcode,
            "store_name": store_name,
            "currency": latest.get("currency") if latest else currency,
            "latest_price": float(latest["price"]) if latest else None,
            "latest_observed_at": latest.get("observed_at") if latest else None,
            "latest_source": latest.get("source") if latest else None,
            "observation_count": observation_count,
            "minimum_price": min(prices) if prices else None,
            "maximum_price": max(prices) if prices else None,
            "confidence": confidence,
            "max_age_days": self.MAX_AGE_DAYS,
        }
