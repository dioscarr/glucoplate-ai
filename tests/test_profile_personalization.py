from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_personalization_client_is_injected_and_cached() -> None:
    response = client.get('/static/index.html')
    assert response.status_code == 200
    assert '<script src="/static/profile-personalization.js" defer></script>' in response.text

    worker = (ROOT / 'app' / 'static' / 'sw.js').read_text(encoding='utf-8')
    assert '/static/profile-personalization.js' in worker


def test_personalization_merges_profile_constraints_into_recipe_request() -> None:
    script = (ROOT / 'app' / 'static' / 'profile-personalization.js').read_text(encoding='utf-8')

    assert "'/api/recipes/generate'" in script
    assert "glucoplate_active_profile_id" in script
    assert 'api.getPreferences(profileId)' in script
    assert 'profile.allergies' in script
    assert 'preferences.dislikes' in script
    assert 'preferences.favorite_cuisines' in script
    assert 'avoid_ingredients:avoid' in script
    assert 'servings:Number.isFinite' in script
    assert 'Strictly exclude allergy ingredients' in script


def test_personalized_recipe_displays_active_profile_label() -> None:
    script = (ROOT / 'app' / 'static' / 'profile-personalization.js').read_text(encoding='utf-8')

    assert 'dataProfileLabel' not in script
    assert 'badge.dataset.profileLabel' in script
    assert 'For ${profile.avatar' in script
    assert 'window.renderRecipe=wrapped' in script


def test_personalization_gracefully_falls_back_without_active_profile() -> None:
    script = (ROOT / 'app' / 'static' / 'profile-personalization.js').read_text(encoding='utf-8')

    assert 'if(!api||!profileId)return null' in script
    assert "console.warn('Profile personalization unavailable'" in script
    assert "console.warn('Recipe personalization skipped'" in script


def test_profile_switch_preserves_enterprise_account_and_admin_navigation() -> None:
    auth = (ROOT / 'app' / 'static' / 'firebase-auth.js').read_text(encoding='utf-8')
    user_data = (ROOT / 'app' / 'static' / 'firebase-user-data.js').read_text(encoding='utf-8')
    assert "const target=profile||document.querySelector('main')" in auth
    assert "Admin dashboard" in auth
    assert "renderPanel" in auth
    assert "GlucoPlateFirebaseAuth?.renderPanel?.()" in user_data
    assert "finally{" in user_data


def test_household_profile_has_mobile_return_to_account_action() -> None:
    user_data = (ROOT / 'app' / 'static' / 'firebase-user-data.js').read_text(encoding='utf-8')
    assert "Back to my account" in user_data
    assert "data-return-account" in user_data
    assert "setActiveProfile('default')" in user_data
    assert "profile-account-return" in user_data
    assert "min-height:44px" in user_data
