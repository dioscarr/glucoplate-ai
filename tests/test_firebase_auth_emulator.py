from __future__ import annotations

import os

import httpx
import pytest


pytestmark = pytest.mark.live


def test_emulator_issued_id_token_is_accepted_by_session_endpoint() -> None:
    emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
    base_url = os.environ.get("AUTH_TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    if not emulator_host:
        pytest.skip("Firebase Auth Emulator is only available in emulator CI")

    emulator_url = f"http://{emulator_host}"
    email = "emulator-user@example.test"
    password = "emulator-password-123"
    with httpx.Client(timeout=30.0) as client:
        created = client.post(
            f"{emulator_url}/identitytoolkit.googleapis.com/v1/accounts:signUp",
            params={"key": "demo-api-key"},
            json={"email": email, "password": password, "returnSecureToken": True},
        )
        created.raise_for_status()
        token = created.json()["idToken"]

        session = client.get(
            f"{base_url}/api/firebase-auth/session",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert session.status_code == 200
    payload = session.json()
    assert payload["user"]["email"] == email
    assert payload["enterprise"] is None
