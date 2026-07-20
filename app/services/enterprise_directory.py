from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Enterprise(Base):
    __tablename__ = "enterprises"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    plan: Mapped[str] = mapped_column(String(40), default="starter")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    memberships: Mapped[list[EnterpriseMembership]] = relationship(
        back_populates="enterprise", cascade="all, delete-orphan"
    )


class EnterpriseUser(Base):
    __tablename__ = "enterprise_users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    memberships: Mapped[list[EnterpriseMembership]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EnterpriseMembership(Base):
    __tablename__ = "enterprise_memberships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    enterprise_id: Mapped[str] = mapped_column(ForeignKey("enterprises.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("enterprise_users.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="member", index=True)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    enterprise: Mapped[Enterprise] = relationship(back_populates="memberships")
    user: Mapped[EnterpriseUser] = relationship(back_populates="memberships")


class EnterpriseRole(Base):
    __tablename__ = "enterprise_roles"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    enterprise_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    permissions_json: Mapped[str] = mapped_column(String(8000), default="[]")
    visibility_json: Mapped[str] = mapped_column(String(8000), default="[]")
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AccessCode(Base):
    __tablename__ = "enterprise_access_codes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    enterprise_id: Mapped[str] = mapped_column(String(64), index=True)
    code_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    label: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "enterprise_audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    enterprise_id: Mapped[str | None] = mapped_column(String(64), index=True)
    actor_uid: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str | None] = mapped_column(String(128))
    details_json: Mapped[str | None] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class EnterpriseDirectory:
    def __init__(self, database_url: str | None = None):
        url = database_url or os.getenv("ENTERPRISE_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not url:
            url = "sqlite:///./glucoplate-enterprise.db"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def create_enterprise(self, *, name: str, slug: str, plan: str = "starter") -> dict[str, Any]:
        enterprise_id = slug
        with self.SessionLocal() as session:
            if session.scalar(select(Enterprise).where((Enterprise.id == enterprise_id) | (Enterprise.slug == slug))):
                raise ValueError("An enterprise with this name or slug already exists")
            item = Enterprise(id=enterprise_id, name=name, slug=slug, plan=plan)
            session.add(item)
            session.commit()
            return {"id": item.id, "name": item.name, "slug": item.slug, "status": item.status, "plan": item.plan, "created_at": item.created_at}

    def create_role(self, enterprise_id: str, *, name: str, permissions: list[str], visibility: list[str]) -> dict[str, Any]:
        with self.SessionLocal() as session:
            if not session.get(Enterprise, enterprise_id):
                raise LookupError("Enterprise not found")
            if session.scalar(select(EnterpriseRole).where(EnterpriseRole.enterprise_id == enterprise_id, EnterpriseRole.name == name)):
                raise ValueError("A role with this name already exists")
            item = EnterpriseRole(enterprise_id=enterprise_id, name=name, permissions_json=json.dumps(sorted(set(permissions))), visibility_json=json.dumps(sorted(set(visibility))))
            session.add(item)
            session.commit()
            return self._role_payload(item)

    def list_roles(self, enterprise_id: str) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            return [self._role_payload(item) for item in session.scalars(select(EnterpriseRole).where(EnterpriseRole.enterprise_id == enterprise_id).order_by(EnterpriseRole.name)).all()]

    def authorization_profile(self, enterprise_id: str, role_name: str) -> dict[str, Any]:
        with self.SessionLocal() as session:
            item = session.scalar(select(EnterpriseRole).where(EnterpriseRole.enterprise_id == enterprise_id, EnterpriseRole.name == role_name, EnterpriseRole.status == "active"))
            if not item:
                return {"role": role_name, "permissions": [], "visibility": []}
            return self._role_payload(item)

    @staticmethod
    def _role_payload(item: EnterpriseRole) -> dict[str, Any]:
        return {"id": item.id, "enterprise_id": item.enterprise_id, "name": item.name, "permissions": json.loads(item.permissions_json), "visibility": json.loads(item.visibility_json), "status": item.status, "created_at": item.created_at, "updated_at": item.updated_at}

    def create_access_code(self, enterprise_id: str, *, label: str | None = None) -> dict[str, Any]:
        code = f"{secrets.randbelow(100000000):08d}"
        with self.SessionLocal() as session:
            if not session.get(Enterprise, enterprise_id):
                raise LookupError("Enterprise not found")
            item = AccessCode(enterprise_id=enterprise_id, code_hash=hashlib.sha256(code.encode()).hexdigest(), label=label)
            session.add(item)
            session.commit()
            return {"id": item.id, "enterprise_id": enterprise_id, "label": item.label, "status": item.status, "created_at": item.created_at, "code": code}

    def list_access_codes(self, enterprise_id: str) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            return [{"id": item.id, "enterprise_id": item.enterprise_id, "label": item.label, "status": item.status, "created_at": item.created_at, "revoked_at": item.revoked_at} for item in session.scalars(select(AccessCode).where(AccessCode.enterprise_id == enterprise_id).order_by(AccessCode.created_at.desc())).all()]

    def seed_enterprise(self, *, enterprise_id: str, name: str, slug: str, plan: str = "starter") -> None:
        with self.SessionLocal() as session:
            if session.get(Enterprise, enterprise_id):
                return
            session.add(Enterprise(id=enterprise_id, name=name, slug=slug, plan=plan))
            session.commit()

    def upsert_authenticated_user(
        self,
        *,
        firebase_uid: str,
        email: str | None,
        display_name: str | None,
        enterprise_id: str,
        role: str,
    ) -> dict[str, Any]:
        with self.SessionLocal() as session:
            enterprise = session.get(Enterprise, enterprise_id)
            if not enterprise or enterprise.status != "active":
                raise ValueError("Enterprise is not active")

            user = session.scalar(select(EnterpriseUser).where(EnterpriseUser.firebase_uid == firebase_uid))
            if not user:
                user = EnterpriseUser(firebase_uid=firebase_uid, email=email, display_name=display_name)
                session.add(user)
                session.flush()
            else:
                user.email = email or user.email
                user.display_name = display_name or user.display_name
                user.status = "active"
            user.last_login_at = _utcnow()

            membership = session.scalar(
                select(EnterpriseMembership).where(
                    EnterpriseMembership.enterprise_id == enterprise_id,
                    EnterpriseMembership.user_id == user.id,
                )
            )
            if not membership:
                membership = EnterpriseMembership(
                    enterprise_id=enterprise_id,
                    user_id=user.id,
                    role=role,
                    status="active",
                )
                session.add(membership)
            else:
                membership.role = role
                membership.status = "active"
            session.commit()
            return self._membership_payload(membership, user, enterprise)

    def list_members(self, enterprise_id: str) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            rows = session.execute(
                select(EnterpriseMembership, EnterpriseUser)
                .join(EnterpriseUser, EnterpriseMembership.user_id == EnterpriseUser.id)
                .where(EnterpriseMembership.enterprise_id == enterprise_id)
                .order_by(EnterpriseUser.email)
            ).all()
            return [self._membership_payload(membership, user, None) for membership, user in rows]

    def update_member(self, enterprise_id: str, user_id: str, *, role: str | None, status: str | None) -> dict[str, Any]:
        with self.SessionLocal() as session:
            membership = session.scalar(
                select(EnterpriseMembership).where(
                    EnterpriseMembership.enterprise_id == enterprise_id,
                    EnterpriseMembership.user_id == user_id,
                )
            )
            if not membership:
                raise LookupError("Membership not found")
            if role:
                membership.role = role
            if status:
                membership.status = status
            user = session.get(EnterpriseUser, user_id)
            session.commit()
            return self._membership_payload(membership, user, None)

    def list_enterprises(self) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            enterprises = session.scalars(select(Enterprise).order_by(Enterprise.name)).all()
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "slug": item.slug,
                    "status": item.status,
                    "plan": item.plan,
                    "created_at": item.created_at,
                }
                for item in enterprises
            ]

    def record_audit(
        self,
        *,
        enterprise_id: str | None,
        actor_uid: str,
        action: str,
        target_type: str,
        target_id: str | None,
        details_json: str | None = None,
    ) -> None:
        with self.SessionLocal() as session:
            session.add(
                AuditEvent(
                    enterprise_id=enterprise_id,
                    actor_uid=actor_uid,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    details_json=details_json,
                )
            )
            session.commit()

    @staticmethod
    def _membership_payload(
        membership: EnterpriseMembership,
        user: EnterpriseUser,
        enterprise: Enterprise | None,
    ) -> dict[str, Any]:
        payload = {
            "membership_id": membership.id,
            "user_id": user.id,
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "display_name": user.display_name,
            "user_status": user.status,
            "role": membership.role,
            "membership_status": membership.status,
            "joined_at": membership.joined_at,
            "last_login_at": user.last_login_at,
        }
        if enterprise:
            payload["enterprise"] = {
                "id": enterprise.id,
                "name": enterprise.name,
                "slug": enterprise.slug,
                "status": enterprise.status,
                "plan": enterprise.plan,
            }
        return payload
