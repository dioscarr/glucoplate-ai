from pathlib import Path

import pytest
from pydantic import ValidationError

from app.api.live_cook_room_routes import JoinRoomPayload


ROOT = Path(__file__).resolve().parents[1]


def test_live_cook_room_routes_are_registered():
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "live_cook_room_router" in source
    assert '"/static/live-cook-rooms.js"' in source
    assert 'version="0.16.0"' in source


def test_room_service_uses_enterprise_scoped_realtime_database():
    source = (ROOT / "app" / "services" / "firebase_live_cook_room_service.py").read_text(encoding="utf-8")
    assert "live_cook_rooms" in source
    assert "live_cook_room_codes" in source
    assert "participants" in source
    assert "activity" in source
    assert "ingredient_checks" in source
    assert "current_step" in source


def test_room_api_supports_mvp_collaboration_actions():
    source = (ROOT / "app" / "api" / "live_cook_room_routes.py").read_text(encoding="utf-8")
    assert '@router.post("")' in source
    assert '@router.post("/join")' in source
    assert '@router.put("/{room_id}/ready")' in source
    assert '@router.patch("/{room_id}/state")' in source
    assert '@router.post("/{room_id}/chat"' in source
    assert '@router.delete("/{room_id}/participants/me")' in source


def test_cook_room_ui_syncs_steps_and_exposes_room_controls():
    source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "Start live room" in source
    assert "Join room" in source
    assert "Need help" in source
    assert "current_step" in source
    assert "invite_code" in source
    assert "setInterval(refresh,1800)" in source


def test_join_payload_normalizes_pasted_invite_codes():
    assert JoinRoomPayload(invite_code=" ab-12 cd ").invite_code == "AB12CD"


def test_join_payload_rejects_codes_that_are_too_short_after_normalization():
    with pytest.raises(ValidationError):
        JoinRoomPayload(invite_code=" - a - ")


def test_live_room_client_exposes_app_state_and_validation_errors():
    index = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
    source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "Object.defineProperties(window" in index
    assert "window.renderCookStep" in index
    assert "function errorMessage" in source
    assert "escapeHtml" in source
    assert "normalizeInviteCode" in source
    assert "Sign in before using a live cook room." in source


def test_live_rooms_refresh_firebase_tokens_before_authenticated_requests():
    auth_source = (ROOT / "app" / "static" / "firebase-auth.js").read_text(encoding="utf-8")
    room_source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "async function getIdToken(forceRefresh=false)" in auth_source
    assert "currentUser" in auth_source
    assert "user.getIdToken(Boolean(forceRefresh))" in auth_source
    assert "GlucoPlateFirebaseAuth={signInGoogle,signOut,syncSession,getAuthClient,getIdToken,showGate}" in auth_source
    assert "response.status===401" in room_source
    assert "request(true)" in room_source


def test_live_room_extensions_render_from_explicit_updates_without_mutation_loops():
    core = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    lifecycle = (ROOT / "app" / "static" / "live-cook-session-lifecycle.js").read_text(encoding="utf-8")
    shared = (ROOT / "app" / "static" / "live-cook-shared-state.js").read_text(encoding="utf-8")
    assert "glucoplate:live-room-updated" in core
    assert "glucoplate:live-room-updated" in lifecycle
    assert "glucoplate:live-room-updated" in shared
    assert "MutationObserver" not in lifecycle
    assert "MutationObserver" not in shared
