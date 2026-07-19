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


def test_livekit_access_tokens_are_room_scoped_and_server_issued():
    source = (ROOT / "app" / "services" / "live_cook_media_service.py").read_text(encoding="utf-8")
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"livekit-api>=1.0.0"' in project
    assert 'os.getenv("LIVEKIT_API_SECRET"' in source
    assert "api.AccessToken(api_key, api_secret)" in source
    assert "api.VideoGrants(" in source
    assert "room_join=True" in source
    assert "can_publish=True" in source
    assert "can_subscribe=True" in source
    assert '"token": token' in source
    assert "api_secret" not in source[source.index("access.update("):]


def test_livekit_client_renders_remote_tracks_and_recovers_connections():
    source = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    styles = (ROOT / "app" / "static" / "live-cook-media.css").read_text(encoding="utf-8")
    assert "livekit-client@2.17.2" in source
    assert "adaptiveStream:true" in source
    assert "dynacast:true" in source
    assert "RoomEvent.TrackSubscribed" in source
    assert "RoomEvent.ParticipantConnected" in source
    assert "RoomEvent.Reconnecting" in source
    assert "setCameraEnabled" in source
    assert "setMicrophoneEnabled" in source
    assert "live-media-grid" in styles
    assert "auto-fit" in styles


def test_pwa_caches_live_media_shell():
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert "glucoplate-shell-v20" in worker
    assert "'/static/live-cook-media.js'" in worker
    assert "'/static/live-cook-media.css'" in worker


def test_video_device_controls_support_livekit_preview_and_mobile_flip():
    source = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    styles = (ROOT / "app" / "static" / "live-cook-media.css").read_text(encoding="utf-8")
    assert "enumerateDevices" in source
    assert "devicechange" in source
    assert "switchActiveDevice" in source
    assert "deviceId:{exact:deviceId}" in source
    assert 'data-media-device="videoinput"' in source
    assert 'data-media-device="audioinput"' in source
    assert "data-media-flip" in source
    assert "flipCamera" in source
    assert "live-media-devices" in styles
    assert "min-height:46px" in styles
