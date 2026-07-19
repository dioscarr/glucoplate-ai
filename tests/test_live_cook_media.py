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
    assert '"serverUrl": server_url' in source
    assert '"participantToken": token' in source
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
    assert "access.serverUrl||access.server_url" in source
    assert "access.participantToken||access.token" in source
    assert "min-height:46px" in styles


def test_same_account_devices_receive_distinct_media_identities():
    routes = (ROOT / "app" / "api" / "live_cook_media_routes.py").read_text(encoding="utf-8")
    service = (ROOT / "app" / "services" / "live_cook_media_service.py").read_text(encoding="utf-8")
    client = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    assert "device_id: str" in routes
    assert "device_label: str | None" in routes
    assert 'identity = f"{enterprise_id}:{uid}:{safe_device_id}"' in service
    assert '"device_id": safe_device_id' in service
    assert '.child(uid).child(safe_device_id).set(record)' in service
    assert "glucoplate_live_media_device_id" in client
    assert "crypto.randomUUID" in client
    assert "device_id:mediaDeviceId" in client
    assert "device_label:mediaDeviceLabel" in client
    assert "media/access?device_id=" in client


def test_pwa_refreshes_multi_device_media_client():
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert "glucoplate-shell-v22" in worker


def test_partial_device_failure_keeps_live_call_connected():
    source = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    assert "Promise.allSettled([liveRoom.localParticipant.setCameraEnabled(true)" in source
    assert "cameraResult.status==='rejected'&&microphoneResult.status==='rejected'" in source
    assert "Camera unavailable. Joining with audio only." in source
    assert "Microphone unavailable. Joining with video only." in source
    assert "openLocalMedia" in source
    assert "new MediaStream(available)" in source
    assert "camera_enabled:cameraEnabled()" in source
    assert "microphone_enabled:microphoneEnabled()" in source


def test_livekit_track_events_are_batched_and_control_errors_are_handled():
    source = (ROOT / "app" / "static" / "live-cook-media.js").read_text(encoding="utf-8")
    assert "function scheduleRender()" in source
    assert "requestAnimationFrame" in source
    assert "const refresh=()=>scheduleRender()" in source
    assert "toggle('audio').catch" in source
    assert "toggle('video').catch" in source
    assert "flipCamera().catch" in source


def test_pwa_refreshes_partial_device_recovery():
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert "glucoplate-shell-v25" in worker
