from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_state_service_enforces_active_session_and_revision() -> None:
    source = read("app/services/live_cook_shared_state_service.py")
    assert 'phase != "active"' in source
    assert "expected_revision" in source
    assert "Room state changed from revision" in source
    assert "ingredient_checks" in source
    assert 'Literal["start", "pause", "resume", "reset"]' in source
    assert "ends_at" in source
    assert "remaining_seconds" in source


def test_shared_state_routes_are_registered() -> None:
    routes = read("app/api/live_cook_shared_state_routes.py")
    main = read("app/main.py")
    assert '@router.put("/{room_id}/ingredients")' in routes
    assert '@router.post("/{room_id}/timer")' in routes
    assert "live_cook_shared_state_router" in main
    assert 'version="0.18.0"' in main
    assert '"/static/live-cook-shared-state.js"' in main


def test_legacy_state_endpoint_cannot_bypass_lifecycle_rules() -> None:
    routes = read("app/api/live_cook_room_routes.py")
    assert 'phase != "active"' in routes
    assert "Use the shared ingredient and timer endpoints" in routes


def test_shared_state_ui_covers_checklist_and_timer_actions() -> None:
    source = read("app/static/live-cook-shared-state.js")
    assert "data-ingredient-index" in source
    assert "expected_revision" in source
    assert 'data-timer-action="pause"' in source
    assert 'data-timer-action="resume"' in source
    assert 'data-timer-action="reset"' in source
    assert "ends_at" in source
    assert "session_status" in source


def test_shared_state_client_uses_fresh_auth_and_explicit_room_updates() -> None:
    source = read("app/static/live-cook-shared-state.js")
    assert "GlucoPlateFirebaseAuth?.getIdToken" in source
    assert "glucoplate:live-room-updated" in source
    assert "MutationObserver" not in source


def test_chef_controls_shared_servings_for_every_participant() -> None:
    service = read("app/services/live_cook_shared_state_service.py")
    room_service = read("app/services/firebase_live_cook_room_service.py")
    routes = read("app/api/live_cook_shared_state_routes.py")
    client = read("app/static/live-cook-shared-state.js")
    assert 'room.get("host_uid")' in service
    assert "Only the Chef can change servings for the room" in service
    assert '"selected_servings": servings' in service
    assert '"servings_changed"' in service
    assert "self._servings(recipe)" in room_service
    assert '@router.put("/{room_id}/servings")' in routes
    assert "data-serving-delta" in client
    assert "Only the Chef can adjust this." in client
    assert "ingredientLabel(item,index,room)" in client


def test_shared_ingredient_checks_use_stable_ids_with_legacy_fallback() -> None:
    room_service = read("app/services/firebase_live_cook_room_service.py")
    shared_service = read("app/services/live_cook_shared_state_service.py")
    routes = read("app/api/live_cook_shared_state_routes.py")
    client = read("app/static/live-cook-shared-state.js")
    assert "def _ingredient_id" in room_service
    assert "self._ingredient_id(recipe, index)" in room_service
    assert "ingredient_id: str | None" in shared_service
    assert 'f"legacy-index-{resolved_index}"' in shared_service
    assert 'checks.pop(str(resolved_index), None)' in shared_service
    assert '"ingredient_id": stable_id' in shared_service
    assert "ingredient_id: str | None" in routes
    assert "data-ingredient-id" in client
    assert "ingredient_id:id" in client
    assert "checks[id]??checks[String(index)]??false" in client
