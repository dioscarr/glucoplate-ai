from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from secrets import token_urlsafe

from app.schemas.auth import (
    AccessCodeLookupResponse,
    AuthResponse,
    CompanyAccessCode,
    RegisterRequest,
    UserRecord,
    UserTypeProfile,
)


class SimpleAuthService:
    """Small local auth provider for the MVP.

    This is intentionally simple and file-backed so registration can be built now without
    requiring Auth0 or Google configuration. The API shape keeps users separate from
    user-type profiles so an existing user can add a new company/access-code profile.
    """

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.seed_path = root / "data" / "mock_access_codes.json"
        self.store_path = Path(
            os.getenv("GLUCOPLATE_AUTH_STORE", str(root / "data" / "runtime_auth_store.json"))
        )

    def lookup_access_code(self, access_code: str) -> AccessCodeLookupResponse:
        company = self._find_company(access_code)
        if company is None:
            return AccessCodeLookupResponse(
                ok=False,
                company=None,
                message="Access code not found. Check the code and try again.",
            )
        return AccessCodeLookupResponse(
            ok=True,
            company=company,
            message=f"Access code matched {company.company_name}.",
        )

    def register(self, request: RegisterRequest) -> AuthResponse:
        company = self._find_company(request.access_code)
        if company is None:
            return AuthResponse(ok=False, status="invalid_access_code", message="Access code not found.")

        data = self._read_store()
        normalized_email = request.email.lower().strip()
        users: list[dict] = data.setdefault("users", [])
        profiles: list[dict] = data.setdefault("user_type_profiles", [])

        user = next((item for item in users if item["email"].lower() == normalized_email), None)
        created_user = False
        if user is None:
            user = {
                "user_id": str(uuid.uuid4()),
                "email": normalized_email,
                "name": request.name.strip(),
                "provider": request.provider or "local",
            }
            users.append(user)
            created_user = True
        elif request.name.strip() and request.name.strip() != user.get("name"):
            user["name"] = request.name.strip()

        profile = next(
            (
                item
                for item in profiles
                if item["user_id"] == user["user_id"]
                and item["access_code"] == company.access_code
                and item["user_type"] == company.user_type
            ),
            None,
        )
        if profile is None:
            profile = {
                "profile_id": str(uuid.uuid4()),
                "user_id": user["user_id"],
                "access_code": company.access_code,
                "company_id": company.company_id,
                "company_name": company.company_name,
                "user_type": company.user_type,
                "user_type_name": company.user_type_name,
                "permissions": company.permissions,
            }
            profiles.append(profile)
            status = "created_user" if created_user else "added_profile"
        else:
            status = "existing_profile"

        self._write_store(data)
        user_profiles = [UserTypeProfile(**item) for item in profiles if item["user_id"] == user["user_id"]]
        token = self._make_demo_token(user["user_id"], profile["profile_id"])
        return AuthResponse(
            ok=True,
            status=status,
            token=token,
            user=UserRecord(**user),
            active_profile=UserTypeProfile(**profile),
            profiles=user_profiles,
            company=company,
            message=self._status_message(status),
        )

    def login(self, email: str) -> AuthResponse:
        data = self._read_store()
        normalized_email = email.lower().strip()
        user = next(
            (item for item in data.get("users", []) if item["email"].lower() == normalized_email),
            None,
        )
        if user is None:
            return AuthResponse(
                ok=False,
                status="user_not_found",
                message="No account found for that email. Register with an access code first.",
            )

        profiles = [
            UserTypeProfile(**item)
            for item in data.get("user_type_profiles", [])
            if item["user_id"] == user["user_id"]
        ]
        active_profile = profiles[0] if profiles else None
        token = self._make_demo_token(user["user_id"], active_profile.profile_id if active_profile else "")
        return AuthResponse(
            ok=True,
            status="logged_in",
            token=token,
            user=UserRecord(**user),
            active_profile=active_profile,
            profiles=profiles,
            message="Signed in with the local demo provider.",
        )

    def list_companies(self) -> list[CompanyAccessCode]:
        return self._read_access_codes()

    def _find_company(self, access_code: str) -> CompanyAccessCode | None:
        normalized = access_code.strip()
        return next((item for item in self._read_access_codes() if item.access_code == normalized), None)

    def _read_access_codes(self) -> list[CompanyAccessCode]:
        payload = json.loads(self.seed_path.read_text(encoding="utf-8"))
        return [CompanyAccessCode(**item) for item in payload.get("access_codes", [])]

    def _read_store(self) -> dict:
        if not self.store_path.exists():
            return {"users": [], "user_type_profiles": []}
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write_store(self, data: dict) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _make_demo_token(self, user_id: str, profile_id: str) -> str:
        return f"demo.{user_id}.{profile_id}.{token_urlsafe(18)}"

    def _status_message(self, status: str) -> str:
        if status == "created_user":
            return "Created user account and profile from access code."
        if status == "added_profile":
            return "Existing user found; added a new company profile."
        return "Existing user and profile found; signed in."
