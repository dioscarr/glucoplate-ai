from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "app" / "static" / "firebase-user-data.js"


def source() -> str:
    return CLIENT.read_text(encoding="utf-8")


def test_recipe_actions_emit_all_flavor_memory_signals() -> None:
    client = source()
    assert "trackInteraction('saved'" in client
    assert "trackInteraction('cooked'" in client
    assert "trackInteraction('dismissed'" in client
    assert "trackInteraction('repeated'" in client
    assert "recipe-save" in client
    assert "cook-mode-completed" in client
    assert "new-recipe-action" in client
    assert "saved-recipe-cook" in client


def test_flavor_memory_signals_include_profile_and_recipe_correlation() -> None:
    client = source()
    assert "profile_id:activeProfileId()" in client
    assert "recipe_id:value.id||value.recipe_id||null" in client
    assert "recipe_name:value.title||value.recipe_name||null" in client
    assert "occurred_at:new Date().toISOString()" in client


def test_flavor_memory_failures_queue_without_blocking_actions() -> None:
    client = source()
    assert "INTERACTION_QUEUE_KEY" in client
    assert "INTERACTION_QUEUE_LIMIT=100" in client
    assert "queueInteraction(payload)" in client
    assert "flushInteractionQueue" in client
    assert "window.addEventListener('online'" in client
    assert "Flavor Memory signal queued for retry." in client


def test_flavor_memory_refreshes_auth_and_deduplicates_rapid_signals() -> None:
    client = source()
    assert "GlucoPlateFirebaseAuth?.getIdToken" in client
    assert "response.status===401" in client
    assert "request(true)" in client
    assert "SIGNAL_DEDUPE_MS=2500" in client
    assert "isDuplicateSignal(payload)" in client


def test_repeat_candidate_resets_when_a_different_recipe_journey_starts() -> None:
    client = source()
    assert "openedFromCookbook=false" in client
    assert "button.id==='generateBtn'" in client
    assert "button.id==='ingredientGenerateBtn'" in client
    assert "button.classList.contains('dish-card')" in client
