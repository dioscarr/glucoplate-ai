from pathlib import Path

import pytest

from app.services.live_cook_session_lifecycle_service import LiveCookSessionLifecycleService


def test_lifecycle_routes_and_service_are_registered() -> None:
    main = Path("app/main.py").read_text(encoding="utf-8")
    routes = Path("app/api/live_cook_session_routes.py").read_text(encoding="utf-8")
    service = Path("app/services/live_cook_session_lifecycle_service.py").read_text(encoding="utf-8")

    assert "live_cook_session_router" in main
    assert '/{room_id}/start' in routes
    assert '/{room_id}/complete' in routes
    assert 'session_status' in service
    assert 'Only the room host' in service


def test_lifecycle_client_exposes_waiting_active_and_completed_states() -> None:
    source = Path("app/static/live-cook-session-lifecycle.js").read_text(encoding="utf-8")

    assert "Waiting for the host" in source
    assert "Cooking in progress" in source
    assert "Session completed" in source
    assert "data-start-session" in source
    assert "data-complete-session" in source


def test_updated_flow_nodes_are_implemented() -> None:
    plan = Path("docs/LIVE_COOKING_FLOW.md").read_text(encoding="utf-8")
    source = Path("app/static/live-cook-session-lifecycle.js").read_text(encoding="utf-8")

    assert "Host starts cooking" in plan
    assert "Session completion" in plan
    assert "start" in source
    assert "complete" in source


class FakeReference:
    def __init__(self, data, path=()):
        self.data = data
        self.path = path

    def child(self, key):
        return FakeReference(self.data, self.path + (str(key),))

    def _parent(self):
        current = self.data
        for key in self.path[:-1]:
            current = current.setdefault(key, {})
        return current

    def get(self):
        current = self.data
        for key in self.path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def set(self, value):
        if not self.path:
            self.data.clear()
            self.data.update(value)
            return
        self._parent()[self.path[-1]] = value

    def update(self, value):
        current = self.get()
        if current is None:
            self.set(dict(value))
        else:
            current.update(value)


def lifecycle_for(data):
    service = LiveCookSessionLifecycleService.__new__(LiveCookSessionLifecycleService)
    reference = FakeReference(data)
    service._room = lambda enterprise_id, room_id: reference
    return service


def active_room():
    return {
        "id": "room-1",
        "session_id": "session-1",
        "host_uid": "chef",
        "title": "Sunday dinner",
        "status": "active",
        "recipe": {"id": "recipe-1", "title": "Green curry"},
        "participants": {
            "chef": {"uid": "chef", "display_name": "Dioscar", "role": "host"},
            "guest": {"uid": "guest", "display_name": "Guest", "role": "participant"},
        },
        "state": {"session_status": "active", "revision": 4},
        "activity": {
            "later": {"id": "later", "type": "timer_start", "message": "Timer started", "created_at": "2026-01-01T12:02:00+00:00"},
            "earlier": {"id": "earlier", "type": "participant_joined", "message": "Guest joined", "created_at": "2026-01-01T12:01:00+00:00"},
        },
    }


def test_terminal_transition_is_idempotent_and_records_one_event():
    data = active_room()
    service = lifecycle_for(data)

    first = service.transition("org", "room-1", "chef", "completed")
    second = service.transition("org", "room-1", "chef", "completed")

    assert first["state"]["session_status"] == "completed"
    assert second["state"]["session_status"] == "completed"
    completed = [item for item in data["activity"].values() if item["type"] == "cooking_session_completed"]
    assert len(completed) == 1
    assert completed[0]["session_id"] == "session-1"
    assert completed[0]["correlation_id"]


def test_history_is_member_only_and_chronological():
    data = active_room()
    service = lifecycle_for(data)

    history = service.history("org", "room-1", "guest")

    assert [item["id"] for item in history["events"]] == ["earlier", "later"]
    assert history["recording"]["enabled"] is False
    with pytest.raises(PermissionError):
        service.history("org", "room-1", "outsider")


def test_abandon_and_post_cook_feedback_are_durable():
    data = active_room()
    service = lifecycle_for(data)

    service.transition("org", "room-1", "chef", "abandoned")
    feedback = service.record_feedback(
        "org",
        "room-1",
        "guest",
        rating=5,
        would_cook_again=True,
        note="  Loved   cooking together. ",
    )
    history = service.history("org", "room-1", "guest")

    assert data["state"]["session_status"] == "abandoned"
    assert feedback["note"] == "Loved cooking together."
    assert history["feedback_summary"]["average_rating"] == 5.0
    assert history["feedback_summary"]["would_cook_again"] == 1
    assert history["my_feedback"]["rating"] == 5


def test_history_routes_and_client_controls_are_present():
    routes = Path("app/api/live_cook_session_routes.py").read_text(encoding="utf-8")
    source = Path("app/static/live-cook-session-lifecycle.js").read_text(encoding="utf-8")

    assert '/{room_id}/abandon' in routes
    assert '/{room_id}/history' in routes
    assert '/{room_id}/feedback' in routes
    assert "data-abandon-session" in source
    assert "data-view-history" in source
    assert "data-post-cook-feedback" in source
    assert "No video was recorded" in source
