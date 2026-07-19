from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.push_notification_service import PushNotificationService

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_push_tokens_persist_in_sqlite(tmp_path, monkeypatch) -> None:
    database = tmp_path / "push_tokens.db"
    monkeypatch.setenv("GLUCOPLATE_PUSH_DB", str(database))

    first = PushNotificationService()
    first.save_token("token-abcdefghijklmnopqrstuvwxyz", user_id="user-1", enterprise_id="glucoplate")

    second = PushNotificationService()
    assert second.token_registered("token-abcdefghijklmnopqrstuvwxyz") is True
    assert database.exists()


def test_native_timer_and_offline_assets_are_injected() -> None:
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert '/static/native-timers.js' in response.text
    assert '/static/offline-actions.js' in response.text


def test_timer_supports_haptic_and_notification_feedback() -> None:
    script = (ROOT / "app" / "static" / "native-timers.js").read_text(encoding="utf-8")
    assert "showNotification" in script
    assert "haptic" in script
    assert "Quick timer" in script


def test_offline_actions_use_indexeddb_and_flush_online() -> None:
    script = (ROOT / "app" / "static" / "offline-actions.js").read_text(encoding="utf-8")
    assert "indexedDB" in script
    assert "pending-actions" in script
    assert "window.addEventListener('online',flush)" in script


def test_apple_touch_icon_sizes_are_registered() -> None:
    script = (ROOT / "app" / "static" / "pwa.js").read_text(encoding="utf-8")
    assert "180x180" in script
    assert "167x167" in script
    assert "152x152" in script


def test_service_worker_caches_new_native_assets() -> None:
    worker = (ROOT / "app" / "static" / "sw.js").read_text(encoding="utf-8")
    assert "/static/native-timers.js" in worker
    assert "/static/offline-actions.js" in worker
