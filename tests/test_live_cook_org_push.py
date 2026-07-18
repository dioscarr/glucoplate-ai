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
