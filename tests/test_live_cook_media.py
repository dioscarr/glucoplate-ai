from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_media_routes_are_registered():
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    routes = (ROOT / "app" / "api" / "live_cook_media_routes.py").read_text(encoding="utf-8")
    assert "live_cook_media_router" in main
    assert '"/static/live-cook-media.js"' in main
    assert '@router.get("/{room_id}/media/access")' in routes
    assert '@router.put("/{room_id}/media/state")' in routes
    assert "Depends(scoped_user)" in routes


def test_media_access_uses_existing_room_identity_and_membership():
    source = (ROOT / "app" / "services" / "live_cook_media_service.py").read_text(encoding="utf-8")
    assert "live_cook_rooms/{room_id}" in source
    assert "uid not in participants" in source
    assert '"room_id": room_id' in source
    assert '"recording": {"enabled": False' in source
    assert "local-preview" in source


def test_media_state_is_separate_from_authoritative_cooking_state():
    source = (ROOT / "app" / "services" / "live_cook_media_service.py").read_text(encoding="utf-8")
    assert 'child("media").child("participants").child(uid)' in source
    assert "camera_enabled" in source
    assert "microphone_enabled" in source
    assert "connection_state" in source


def test_client_handles_permissions_controls_and_non_video_fallback():
    source = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    assert "navigator.mediaDevices?.getUserMedia" in source
    assert "NotAllowedError" in source
    assert "Cooking controls still work" in source
    assert "data-media-mic" in source
    assert "data-media-camera" in source
    assert "data-media-leave" in source
    assert "pagehide" in source


def test_core_polling_preserves_media_preview_node():
    source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "media=body.querySelector('[data-live-media]')" in source
    assert "if(media)body.prepend(media)" in source
