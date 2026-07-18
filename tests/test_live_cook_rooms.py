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


def test_mobile_lifecycle_uses_delegated_in_app_confirmation():
    source = (ROOT / "app" / "static" / "live-cook-session-lifecycle.js").read_text(encoding="utf-8")
    assert "body.addEventListener('click',handleClick)" in source
    assert "data-confirm-complete" in source
    assert "role=\"alertdialog\"" in source
    assert "confirm(" not in source
    assert "response.status===401" in source


def test_live_room_has_touch_friendly_mobile_styles():
    room_source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    css = (ROOT / "app" / "static" / "live-cook-room-premium.css").read_text(encoding="utf-8")
    assert "/static/live-cook-room-premium.css" in room_source
    assert "@media(max-width:640px)" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "min-height:44px" in css


def test_enterprise_live_room_directory_and_direct_join_routes():
    routes = (ROOT / "app" / "api" / "live_cook_room_routes.py").read_text(encoding="utf-8")
    service = (ROOT / "app" / "services" / "firebase_live_cook_room_service.py").read_text(encoding="utf-8")
    assert '@router.get("/active")' in routes
    assert '@router.post("/join/{room_id}")' in routes
    assert "list_active_rooms" in service
    assert "join_room_by_id" in service
    assert 'room.get("status") != "active"' in service
    assert 'phase == "completed"' in service


def test_notification_deep_link_auto_joins_without_invite_entry():
    notifications = (ROOT / "app" / "api" / "live_cook_session_routes.py").read_text(encoding="utf-8")
    client = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "?live_room=" in notifications
    assert "consumeLiveRoomDeepLink" in client
    assert "/api/live-cook-rooms/join/" in client
    assert "history.replaceState" in client


def test_live_now_directory_supports_switching_rooms():
    client = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    css = (ROOT / "app" / "static" / "live-cook-room-premium.css").read_text(encoding="utf-8")
    assert "Live now" in client
    assert "browseLiveRooms" in client
    assert "data-join-room-id" in client
    assert ".live-room-directory-card" in css
