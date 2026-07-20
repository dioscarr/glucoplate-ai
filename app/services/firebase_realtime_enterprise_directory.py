from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


class FirebaseRealtimeEnterpriseDirectory:
    """Realtime Database persistence for enterprises, users, memberships, and audit events.

    All access is server-side through the Firebase Admin SDK. Browser clients never read or
    write these paths directly.
    """

    def __init__(self, root_path: str = "enterprise_directory"):
        app = FirebaseAuthService().firebase_app()
        self.root = db.reference(root_path.strip("/"), app=app)

    def create_schema(self) -> None:
        # Realtime Database is schemaless. Keeping this method preserves the directory contract.
        return None

    def create_enterprise(self, *, name: str, slug: str, plan: str = "starter") -> dict[str, Any]:
        enterprise_id = slug
        ref = self.root.child("enterprises").child(enterprise_id)
        if ref.get() or any(item.get("name", "").lower() == name.lower() for item in (self.root.child("enterprises").get() or {}).values()):
            raise ValueError("An enterprise with this name or slug already exists")
        now = _utcnow()
        item = {"id": enterprise_id, "name": name, "slug": slug, "status": "active", "plan": plan, "created_at": now, "updated_at": now}
        ref.set(item)
        return item

    def create_role(self, enterprise_id: str, *, name: str, permissions: list[str], visibility: list[str]) -> dict[str, Any]:
        if not self.root.child("enterprises").child(enterprise_id).get():
            raise LookupError("Enterprise not found")
        role_id = uuid.uuid4().hex
        item = {"id": role_id, "enterprise_id": enterprise_id, "name": name, "permissions": sorted(set(permissions)), "visibility": sorted(set(visibility)), "status": "active", "created_at": _utcnow(), "updated_at": _utcnow()}
        self.root.child("roles").child(enterprise_id).child(role_id).set(item)
        return item

    def list_roles(self, enterprise_id: str) -> list[dict[str, Any]]:
        roles = self.root.child("roles").child(enterprise_id).get() or {}
        return sorted(roles.values(), key=lambda item: item.get("name", "").lower())

    def authorization_profile(self, enterprise_id: str, role_name: str) -> dict[str, Any]:
        return next((item for item in self.list_roles(enterprise_id) if item.get("name") == role_name and item.get("status") == "active"), {"role": role_name, "permissions": [], "visibility": []})

    def create_access_code(self, enterprise_id: str, *, label: str | None = None) -> dict[str, Any]:
        if not self.root.child("enterprises").child(enterprise_id).get():
            raise LookupError("Enterprise not found")
        code = f"{secrets.randbelow(100000000):08d}"
        code_id = uuid.uuid4().hex
        item = {"id": code_id, "enterprise_id": enterprise_id, "code_hash": hashlib.sha256(code.encode()).hexdigest(), "label": label, "status": "active", "created_at": _utcnow()}
        self.root.child("access_codes").child(code_id).set(item)
        return {**{key: value for key, value in item.items() if key != "code_hash"}, "code": code}

    def list_access_codes(self, enterprise_id: str) -> list[dict[str, Any]]:
        items = self.root.child("access_codes").get() or {}
        return sorted([{key: value for key, value in item.items() if key != "code_hash"} for item in items.values() if item.get("enterprise_id") == enterprise_id], key=lambda item: item.get("created_at", ""), reverse=True)

    def seed_enterprise(self, *, enterprise_id: str, name: str, slug: str, plan: str = "starter") -> None:
        ref = self.root.child("enterprises").child(enterprise_id)
        if ref.get():
            return
        now = _utcnow()
        ref.set(
            {
                "id": enterprise_id,
                "name": name,
                "slug": slug,
                "status": "active",
                "plan": plan,
                "created_at": now,
                "updated_at": now,
            }
        )

    def upsert_authenticated_user(
        self,
        *,
        firebase_uid: str,
        email: str | None,
        display_name: str | None,
        enterprise_id: str,
        role: str,
    ) -> dict[str, Any]:
        enterprise = self.root.child("enterprises").child(enterprise_id).get()
        if not enterprise or enterprise.get("status") != "active":
            raise ValueError("Enterprise is not active")

        now = _utcnow()
        user_ref = self.root.child("users").child(firebase_uid)
        existing_user = user_ref.get() or {}
        user = {
            "id": firebase_uid,
            "firebase_uid": firebase_uid,
            "email": email or existing_user.get("email"),
            "display_name": display_name or existing_user.get("display_name"),
            "status": "active",
            "created_at": existing_user.get("created_at") or now,
            "updated_at": now,
            "last_login_at": now,
        }
        user_ref.set(user)

        membership_ref = self.root.child("memberships").child(enterprise_id).child(firebase_uid)
        existing_membership = membership_ref.get() or {}
        membership = {
            "id": existing_membership.get("id") or uuid.uuid4().hex,
            "enterprise_id": enterprise_id,
            "user_id": firebase_uid,
            "role": role,
            "status": "active",
            "joined_at": existing_membership.get("joined_at") or now,
            "updated_at": now,
        }
        membership_ref.set(membership)
        self.root.child("user_enterprises").child(firebase_uid).child(enterprise_id).set(True)
        return self._membership_payload(membership, user, enterprise)

    def list_members(self, enterprise_id: str) -> list[dict[str, Any]]:
        memberships = self.root.child("memberships").child(enterprise_id).get() or {}
        users_root = self.root.child("users")
        results: list[dict[str, Any]] = []
        for user_id, membership in memberships.items():
            user = users_root.child(user_id).get()
            if user:
                results.append(self._membership_payload(membership, user, None))
        return sorted(results, key=lambda item: (item.get("email") or "").lower())

    def update_member(
        self,
        enterprise_id: str,
        user_id: str,
        *,
        role: str | None,
        status: str | None,
    ) -> dict[str, Any]:
        membership_ref = self.root.child("memberships").child(enterprise_id).child(user_id)
        membership = membership_ref.get()
        if not membership:
            raise LookupError("Membership not found")

        updates: dict[str, Any] = {"updated_at": _utcnow()}
        if role:
            updates["role"] = role
        if status:
            updates["status"] = status
        membership_ref.update(updates)
        membership.update(updates)

        user = self.root.child("users").child(user_id).get()
        if not user:
            raise LookupError("Enterprise user not found")
        return self._membership_payload(membership, user, None)

    def list_enterprises(self) -> list[dict[str, Any]]:
        enterprises = self.root.child("enterprises").get() or {}
        return sorted(enterprises.values(), key=lambda item: (item.get("name") or "").lower())

    def record_audit(
        self,
        *,
        enterprise_id: str | None,
        actor_uid: str,
        action: str,
        target_type: str,
        target_id: str | None,
        details_json: str | None = None,
    ) -> None:
        event_id = uuid.uuid4().hex
        details: Any = details_json
        if details_json:
            try:
                details = json.loads(details_json)
            except json.JSONDecodeError:
                pass
        self.root.child("audit_events").child(event_id).set(
            {
                "id": event_id,
                "enterprise_id": enterprise_id,
                "actor_uid": actor_uid,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "details": details,
                "created_at": _utcnow(),
            }
        )

    @staticmethod
    def _membership_payload(
        membership: dict[str, Any],
        user: dict[str, Any],
        enterprise: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = {
            "membership_id": membership.get("id"),
            "user_id": user.get("id") or user.get("firebase_uid"),
            "firebase_uid": user.get("firebase_uid"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "user_status": user.get("status", "active"),
            "role": membership.get("role", "member"),
            "membership_status": membership.get("status", "active"),
            "joined_at": membership.get("joined_at"),
            "last_login_at": user.get("last_login_at"),
        }
        if enterprise:
            payload["enterprise"] = {
                "id": enterprise.get("id"),
                "name": enterprise.get("name"),
                "slug": enterprise.get("slug"),
                "status": enterprise.get("status"),
                "plan": enterprise.get("plan"),
            }
        return payload
