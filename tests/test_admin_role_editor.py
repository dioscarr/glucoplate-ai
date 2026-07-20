from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_loads_modular_role_editor():
    html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
    assert 'data-view="roles"' in html
    assert 'id="rolesView"' in html
    assert 'id="roleCreateForm"' in html
    assert 'id="permissionGroups"' in html
    assert 'id="featureChoices"' in html
    assert '/static/admin-roles.js' in html
    assert '/static/admin-roles.css' in html


def test_role_editor_integrates_role_and_authorization_profile_apis():
    source = (ROOT / "app" / "static" / "admin-roles.js").read_text(encoding="utf-8")
    assert "/api/enterprise/admin/roles" in source
    assert "/api/enterprise/authorization/profile" in source
    assert "permissions:" in source
    assert "visibility:" in source
    assert "roles.manage" in source
    assert "live_kitchen" in source


def test_role_editor_has_accessible_responsive_contracts():
    html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
    css = (ROOT / "app" / "static" / "admin-roles.css").read_text(encoding="utf-8")
    assert 'aria-labelledby="roleEditorTitle"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert "focus-visible" in css
    assert "@media(max-width:980px)" in css
    assert "@media(max-width:560px)" in css
