from pathlib import Path

from app.services.push_notification_service import PushNotificationService


ROOT = Path(__file__).resolve().parents[1]


def test_push_subscription_is_scoped_to_authenticated_enterprise(tmp_path, monkeypatch):
    monkeypatch.setenv("GLUCOPLATE_PUSH_DB", str(tmp_path / "push.db"))
    monkeypatch.setenv("GLUCOPLATE_PUSH_STORE", str(tmp_path / "legacy.json"))
    service = PushNotificationService()
    saved = service.save_token(
        "enterprise-device-token-1234567890",
        user_id="cook-1",
        enterprise_id="org-1",
    )
    assert saved["enterprise_id"] == "org-1"


def test_live_session_start_schedules_enterprise_push():
    source = (ROOT / "app" / "api" / "live_cook_session_routes.py").read_text(encoding="utf-8")
    assert "background_tasks.add_task" in source
    assert "notify_enterprise_session_started" in source
    assert 'enterprise_id=user.enterprise_id' not in source
    assert "enterprise_id=enterprise_id" in source
    assert "Live cooking started" in source
    assert "join_room=" in source


def test_push_delivery_supports_enterprise_filtering():
    source = (ROOT / "app" / "services" / "push_notification_service.py").read_text(encoding="utf-8")
    assert "enterprise_id TEXT" in source
    assert 'ALTER TABLE push_tokens ADD COLUMN enterprise_id TEXT' in source
    assert "if enterprise_id:" in source
    assert 'item.get("enterprise_id") == enterprise_id' in source


def test_existing_pwa_tokens_refresh_their_enterprise_scope():
    source = (ROOT / "app" / "static" / "pwa.js").read_text(encoding="utf-8")
    assert "refreshStoredTokenRegistration" in source
    assert "glucoplate_fcm_token" in source
    assert "refreshStoredTokenRegistration();renderPwaPanel()" in source


def test_live_room_minimize_survives_polling_and_can_reopen():
    source = (ROOT / "app" / "static" / "live-cook-rooms.js").read_text(encoding="utf-8")
    assert "dismissed=false" in source
    assert "panel.hidden=dismissed" in source
    assert "setDismissed(true)" in source
    assert "liveRoomReopen" in source


def test_mobile_live_room_body_is_independently_scrollable():
    css = (ROOT / "app" / "static" / "live-cook-room-premium.css").read_text(encoding="utf-8")
    assert "overflow-y:auto" in css
    assert "-webkit-overflow-scrolling:touch" in css
    assert "touch-action:pan-y" in css
    assert "height:88dvh" in css


def test_enterprise_push_subscriptions_use_firebase_persistence():
    source = (ROOT / "app" / "services" / "push_notification_service.py").read_text(encoding="utf-8")
    assert "app_data/enterprises/{enterprise_id}/push_tokens" in source
    assert "hashlib.sha256" in source
    assert "matched" in source
    assert 'headers={"Urgency": "high"}' in source
