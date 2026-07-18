from pathlib import Path


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
