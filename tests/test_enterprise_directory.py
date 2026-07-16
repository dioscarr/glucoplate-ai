from pathlib import Path

import pytest

from app.services.enterprise_directory import EnterpriseDirectory


def build_directory(tmp_path: Path) -> EnterpriseDirectory:
    directory = EnterpriseDirectory(f"sqlite:///{tmp_path / 'enterprise-test.db'}")
    directory.create_schema()
    directory.seed_enterprise(
        enterprise_id="glucoplate",
        name="GlucoPlate AI",
        slug="glucoplate",
        plan="enterprise",
    )
    directory.seed_enterprise(
        enterprise_id="acme",
        name="Acme Kitchens",
        slug="acme-kitchens",
    )
    return directory


def test_authenticated_user_creates_membership(tmp_path: Path):
    directory = build_directory(tmp_path)

    membership = directory.upsert_authenticated_user(
        firebase_uid="firebase-1",
        email="owner@example.com",
        display_name="Owner",
        enterprise_id="glucoplate",
        role="enterprise_owner",
    )

    assert membership["enterprise"]["id"] == "glucoplate"
    assert membership["role"] == "enterprise_owner"
    assert membership["membership_status"] == "active"


def test_members_are_isolated_by_enterprise(tmp_path: Path):
    directory = build_directory(tmp_path)
    directory.upsert_authenticated_user(
        firebase_uid="firebase-1",
        email="one@example.com",
        display_name="One",
        enterprise_id="glucoplate",
        role="member",
    )
    directory.upsert_authenticated_user(
        firebase_uid="firebase-2",
        email="two@example.com",
        display_name="Two",
        enterprise_id="acme",
        role="member",
    )

    glucoplate_users = directory.list_members("glucoplate")
    acme_users = directory.list_members("acme")

    assert [user["email"] for user in glucoplate_users] == ["one@example.com"]
    assert [user["email"] for user in acme_users] == ["two@example.com"]


def test_admin_can_change_role_and_disable_membership(tmp_path: Path):
    directory = build_directory(tmp_path)
    created = directory.upsert_authenticated_user(
        firebase_uid="firebase-1",
        email="member@example.com",
        display_name="Member",
        enterprise_id="glucoplate",
        role="member",
    )

    updated = directory.update_member(
        "glucoplate",
        created["user_id"],
        role="manager",
        status="disabled",
    )

    assert updated["role"] == "manager"
    assert updated["membership_status"] == "disabled"


def test_unknown_enterprise_is_rejected(tmp_path: Path):
    directory = build_directory(tmp_path)

    with pytest.raises(ValueError, match="Enterprise is not active"):
        directory.upsert_authenticated_user(
            firebase_uid="firebase-1",
            email="user@example.com",
            display_name="User",
            enterprise_id="missing",
            role="member",
        )
