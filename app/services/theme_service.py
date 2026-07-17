from __future__ import annotations

import json
import os
import re
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from firebase_admin import db

from app.services.firebase_auth_service import FirebaseAuthService

DEFAULT_THEME: dict[str, Any] = {
    "id": "default",
    "name": "Default",
    "version": 1,
    "status": "published",
    "enabled": True,
    "tokens": {
        "colors": {
            "background": "#f7f4ef",
            "surface": "#ffffff",
            "surfaceAlt": "#f3ede6",
            "text": "#211f1d",
            "muted": "#756f69",
            "border": "#e7ded4",
            "primary": "#f26a2e",
            "secondary": "#ff9e3d",
            "accent": "#257453",
            "danger": "#a92f24",
            "dark": "#171412",
        },
        "typography": {
            "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
            "baseSize": 16,
            "baseWeight": 400,
            "headingWeight": 900,
        },
        "shape": {"radius": 26, "controlRadius": 17, "borderWidth": 1},
        "effects": {
            "shadow": "0 18px 50px rgba(59,43,30,.12)",
            "softShadow": "0 10px 28px rgba(59,43,30,.08)",
            "textShadow": "none",
        },
    },
    "sections": {},
    "components": {},
    "elements": {},
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _theme_id(name: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "theme").lower()).strip("-")
    return f"{slug or 'theme'}-{uuid.uuid4().hex[:8]}"


class ThemeService:
    """Company theme persistence.

    Firebase Realtime Database is the production source of truth. A local JSON fallback is
    retained for development and tests when Firebase Realtime Database is not configured.
    """

    def __init__(self, path: str | None = None, root_path: str = "enterprise_themes") -> None:
        self._lock = RLock()
        self.path = Path(path or os.getenv("THEME_STORE_PATH", ".data/company-themes.json"))
        firebase = FirebaseAuthService()
        self.root = None
        if firebase.realtime_database_configured():
            self.root = db.reference(root_path.strip("/"), app=firebase.firebase_app())

    def _read_local(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_local(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)

    def _read_company(self, enterprise_id: str) -> dict[str, Any]:
        if self.root is not None:
            return self.root.child(enterprise_id).get() or {}
        return self._read_local().get(enterprise_id, {})

    def _write_company(self, enterprise_id: str, company: dict[str, Any]) -> None:
        if self.root is not None:
            self.root.child(enterprise_id).set(company)
            return
        data = self._read_local()
        data[enterprise_id] = company
        self._write_local(data)

    def _normalize(self, enterprise_id: str, theme_id: str, stored: dict[str, Any] | None) -> dict[str, Any]:
        theme = deepcopy(DEFAULT_THEME)
        if stored:
            theme.update(deepcopy(stored))
        theme["id"] = theme_id
        theme["enterpriseId"] = enterprise_id
        theme.setdefault("name", "Default" if theme_id == "default" else theme_id.replace("-", " ").title())
        theme.setdefault("enabled", True)
        return theme

    def list(self, enterprise_id: str, *, enabled_only: bool = False) -> dict[str, Any]:
        with self._lock:
            company = self._read_company(enterprise_id)
            stored_themes = company.get("themes") or {}
            if not stored_themes:
                stored_themes = {"default": deepcopy(DEFAULT_THEME)}
            items = [self._normalize(enterprise_id, key, value) for key, value in stored_themes.items()]
            if enabled_only:
                items = [item for item in items if item.get("enabled", True) and item.get("status") == "published"]
            active_id = company.get("active_theme_id") or "default"
            if not any(item["id"] == active_id for item in items):
                active_id = items[0]["id"] if items else "default"
            return {"enterpriseId": enterprise_id, "activeThemeId": active_id, "themes": items}

    def get(self, enterprise_id: str, theme_id: str | None = None) -> dict[str, Any]:
        bundle = self.list(enterprise_id)
        selected_id = theme_id or bundle["activeThemeId"]
        selected = next((item for item in bundle["themes"] if item["id"] == selected_id), None)
        return selected or self._normalize(enterprise_id, "default", None)

    def create(self, enterprise_id: str, *, name: str, source_theme_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            company = self._read_company(enterprise_id)
            themes = company.setdefault("themes", {})
            theme_id = _theme_id(name)
            source = self.get(enterprise_id, source_theme_id)
            created = deepcopy(source)
            created.update({"id": theme_id, "name": name.strip() or "Untitled theme", "version": 1, "status": "draft", "enabled": False, "created_at": _utcnow(), "updated_at": _utcnow()})
            created.pop("enterpriseId", None)
            themes[theme_id] = created
            company.setdefault("active_theme_id", "default")
            self._write_company(enterprise_id, company)
            return self._normalize(enterprise_id, theme_id, created)

    def save(self, enterprise_id: str, theme: dict[str, Any], *, theme_id: str | None = None, publish: bool = False) -> dict[str, Any]:
        with self._lock:
            company = self._read_company(enterprise_id)
            themes = company.setdefault("themes", {})
            selected_id = theme_id or theme.get("id") or company.get("active_theme_id") or "default"
            current = themes.get(selected_id, {})
            saved = deepcopy(theme)
            saved.pop("enterpriseId", None)
            saved["id"] = selected_id
            saved["name"] = saved.get("name") or current.get("name") or ("Default" if selected_id == "default" else selected_id.replace("-", " ").title())
            saved["version"] = int(current.get("version", 0)) + 1
            saved["status"] = "published" if publish else "draft"
            saved["enabled"] = bool(saved.get("enabled", current.get("enabled", publish)))
            if publish:
                saved["enabled"] = True
                saved["published_at"] = _utcnow()
            saved["updated_at"] = _utcnow()
            saved["created_at"] = current.get("created_at") or saved["updated_at"]
            themes[selected_id] = saved
            company.setdefault("active_theme_id", selected_id if publish else "default")
            self._write_company(enterprise_id, company)
            return self._normalize(enterprise_id, selected_id, saved)

    def activate(self, enterprise_id: str, theme_id: str) -> dict[str, Any]:
        with self._lock:
            company = self._read_company(enterprise_id)
            theme = (company.get("themes") or {}).get(theme_id)
            if not theme and theme_id != "default":
                raise LookupError("Theme not found")
            normalized = self._normalize(enterprise_id, theme_id, theme)
            if normalized.get("status") != "published" or not normalized.get("enabled", True):
                raise ValueError("Only enabled, published themes can be activated")
            company.setdefault("themes", {})
            if theme_id == "default" and theme_id not in company["themes"]:
                default = deepcopy(DEFAULT_THEME)
                default["updated_at"] = _utcnow()
                company["themes"][theme_id] = default
            company["active_theme_id"] = theme_id
            company["updated_at"] = _utcnow()
            self._write_company(enterprise_id, company)
            return normalized

    def delete(self, enterprise_id: str, theme_id: str) -> dict[str, Any]:
        if theme_id == "default":
            raise ValueError("The default theme cannot be deleted")
        with self._lock:
            company = self._read_company(enterprise_id)
            themes = company.get("themes") or {}
            if theme_id not in themes:
                raise LookupError("Theme not found")
            themes.pop(theme_id)
            if company.get("active_theme_id") == theme_id:
                company["active_theme_id"] = "default"
            company["themes"] = themes
            self._write_company(enterprise_id, company)
            return self.get(enterprise_id)

    def reset(self, enterprise_id: str, theme_id: str | None = None) -> dict[str, Any]:
        selected_id = theme_id or "default"
        with self._lock:
            company = self._read_company(enterprise_id)
            company.setdefault("themes", {})[selected_id] = deepcopy(DEFAULT_THEME) | {
                "id": selected_id,
                "name": "Default" if selected_id == "default" else selected_id.replace("-", " ").title(),
                "updated_at": _utcnow(),
            }
            company.setdefault("active_theme_id", "default")
            self._write_company(enterprise_id, company)
            return self.get(enterprise_id, selected_id)
