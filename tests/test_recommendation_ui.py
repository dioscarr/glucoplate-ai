from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_html_receives_recommendation_ui_script() -> None:
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert '<script src="/static/recommendation-ui.js" defer></script>' in response.text


def test_recommendation_ui_wraps_generation_and_preserves_fallback() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")

    assert "/api/recommendations/recipe-concepts" in script
    assert "window.generateRecipe=recommendBeforeGenerate" in script
    assert "originalGenerate" in script
    assert "why_this_fits" in script
    assert "profile_id:activeProfileId()" in script


def test_service_worker_caches_recommendation_ui() -> None:
    response = client.get("/static/sw.js")

    assert response.status_code == 200
    assert "/static/recommendation-ui.js" in response.text
    assert "const CACHE='glucoplate-shell-v" in response.text


def test_concept_flow_shows_three_ranked_directions_with_trust_context() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")
    assert "limit:3" in script
    assert "Flavor Memory signals" in script
    assert "pantry items considered" in script
    assert "use-soon matches" in script
    assert "These are ranked suggestions—not guarantees." in script


def test_concept_reasons_render_as_clear_trust_chips() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")
    assert "const reasonList=concept" in script
    assert "Array.isArray(concept.why_this_fits)" in script
    assert "reasonList(concept).slice(0,2)" in script
    assert 'class="concept-reasons"' in script


def test_every_concept_dismissal_records_a_skip_reason() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")
    assert "function dismissConcepts" in script
    assert "close_button" in script
    assert "backdrop" in script
    assert "escape_key" in script
    assert "user_requested_direct_generation" in script
    assert "event.key==='Escape'" in script


def test_recommendation_feedback_stays_on_original_profile() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")
    assert "profileId:result?.profile_id||activeProfileId()" in script
    assert "profile_id:profileId" in script
    assert "value.profileId" in script


def test_concept_requests_refresh_auth_and_timeout_to_direct_generation() -> None:
    script = (ROOT / "app" / "static" / "recommendation-ui.js").read_text(encoding="utf-8")
    assert "GlucoPlateFirebaseAuth?.getIdToken" in script
    assert "response.status===401" in script
    assert "request(true)" in script
    assert "new AbortController()" in script
    assert "12000" in script
    assert "Personalized suggestions were unavailable. Generating directly." in script
