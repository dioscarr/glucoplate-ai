from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_recommendation_api_exposes_feedback_contracts() -> None:
    routes = (ROOT / "app" / "api" / "recommendation_routes.py").read_text(encoding="utf-8")

    assert '@router.post("/sessions")' in routes
    assert '@router.post("/events")' in routes
    assert '@router.get("/history")' in routes
    assert '"session_id": session["id"]' in routes
    assert '"event_type": "impression"' in routes


def test_recommendation_ui_records_selection_skip_and_generation() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")

    assert "/api/recommendations/events" in script
    assert "'selected'" in script
    assert "'skipped'" in script
    assert "'generated'" in script
    assert "session_id:sessionId" in script
    assert "console.debug('Recommendation feedback was not recorded.'" in script


def test_feedback_storage_is_profile_scoped_and_validated() -> None:
    service = (ROOT / "app" / "services" / "firebase_user_data_service.py").read_text(encoding="utf-8")

    assert 'RECOMMENDATION_EVENT_TYPES = {"impression", "selected", "skipped", "generated"}' in service
    assert 'f"recommendation_sessions/{session_id}"' in service
    assert 'f"recommendation_events/{event_id}"' in service
    assert 'raise ValueError("Recommendation session was not found")' in service
    assert '"selection_rate"' in service
