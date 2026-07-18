from pathlib import Path


SOURCE = Path("app/static/live-cook-shared-state.js").read_text(encoding="utf-8")


def test_shared_controls_use_delegated_events() -> None:
    assert "body.addEventListener('change',handleInteraction)" in SOURCE
    assert "body.addEventListener('click',handleInteraction)" in SOURCE
    assert "data.sharedStateHandlers" in SOURCE


def test_shared_controls_retry_authentication_and_stale_revisions() -> None:
    assert "response.status===401" in SOURCE
    assert "getIdToken" in SOURCE
    assert "error.status===409&&retry" in SOURCE
    assert "expected_revision:Number(room.state?.revision||0)" in SOURCE


def test_shared_controls_resolve_latest_room_at_interaction_time() -> None:
    assert "window.GlucoPlateLiveCookRooms?.getRoom?.()" in SOURCE
    assert "await window.GlucoPlateLiveCookRooms?.refresh?.()" in SOURCE
    assert "inputmode=\"numeric\"" in SOURCE
