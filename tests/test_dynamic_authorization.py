from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api import enterprise_admin_routes as routes

ROOT = Path(__file__).resolve().parents[1]


class FakeDirectory:
    def __init__(self, profile):
        self.profile = profile

    def authorization_profile(self, enterprise_id, role):
        return {"role": role, "permissions": [], "visibility": [], **self.profile}


def test_permission_registry_documents_all_admin_capabilities():
    assert set(routes.PERMISSION_REGISTRY) == {
        "enterprise.users.read",
        "enterprise.users.write",
        "enterprise.themes.read",
        "enterprise.themes.write",
        "enterprise.roles.read",
        "enterprise.roles.write",
        "platform.enterprises.read",
        "platform.enterprises.write",
    }


def test_builtin_admin_permissions_remain_backward_compatible(monkeypatch):
    monkeypatch.setattr(routes, "directory", lambda: FakeDirectory({}))
    user = routes.AuthContext(uid="owner", enterprise_id="acme", role="enterprise_owner")
    profile = routes.resolved_authorization_profile(user)
    assert "enterprise.users.write" in profile["permissions"]
    assert "platform.enterprises.read" not in profile["permissions"]


def test_custom_role_uses_explicit_dynamic_permissions(monkeypatch):
    monkeypatch.setattr(
        routes,
        "directory",
        lambda: FakeDirectory({"permissions": ["enterprise.users.read"], "visibility": ["users"]}),
    )
    user = routes.AuthContext(uid="auditor", enterprise_id="acme", role="auditor")
    profile = routes.resolved_authorization_profile(user)
    assert profile["permissions"] == ["enterprise.users.read"]
    assert profile["visibility"] == ["users"]

    read_dependency = routes.require_permission("enterprise.users.read")
    assert read_dependency(user).uid == "auditor"
    with pytest.raises(HTTPException) as exc:
        routes.require_permission("enterprise.users.write")(user)
    assert exc.value.status_code == 403


def test_admin_frontend_uses_runtime_profile_and_contains_no_escaped_newline_token():
    source = (ROOT / "app" / "static" / "admin.js").read_text(encoding="utf-8")
    runtime = (ROOT / "app" / "static" / "admin-authorization.js").read_text(encoding="utf-8")
    html = (ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
    assert "/api/enterprise/authorization/profile" in runtime
    assert "window.GlucoPlateAuthorization" in runtime
    assert html.index("admin-authorization.js") < html.index("admin.js")
    assert "can('enterprise.users.read')" in source
    assert "can('platform.enterprises.read')" in source
    assert ");\\\\n    byId(" not in source


def test_feature_endpoints_use_dynamic_permission_dependencies():
    source = (ROOT / "app" / "api" / "enterprise_admin_routes.py").read_text(encoding="utf-8")
    assert 'Depends(require_permission("enterprise.users.read"))' in source
    assert 'Depends(require_permission("enterprise.users.write"))' in source
    assert 'Depends(require_permission("enterprise.themes.write"))' in source
    assert 'Depends(require_permission("enterprise.roles.write"))' in source
    assert 'Depends(require_permission("platform.enterprises.write"))' in source
