from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

DEFAULT_THEME: dict[str, Any] = {
    "version": 1,
    "status": "published",
    "tokens": {
        "colors": {
            "background": "#f7f4ef", "surface": "#ffffff", "surfaceAlt": "#f3ede6",
            "text": "#211f1d", "muted": "#756f69", "border": "#e7ded4",
            "primary": "#f26a2e", "secondary": "#ff9e3d", "accent": "#257453",
            "danger": "#a92f24", "dark": "#171412"
        },
        "typography": {"fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif", "baseSize": 16, "baseWeight": 400, "headingWeight": 900},
        "shape": {"radius": 26, "controlRadius": 17, "borderWidth": 1},
        "effects": {"shadow": "0 18px 50px rgba(59,43,30,.12)", "softShadow": "0 10px 28px rgba(59,43,30,.08)", "textShadow": "none"}
    },
    "sections": {},
    "components": {},
    "elements": {},
}

class ThemeService:
    def __init__(self, path: str | None = None) -> None:
        configured = path or os.getenv("THEME_STORE_PATH", ".data/company-themes.json")
        self.path = Path(configured)
        self._lock = RLock()

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)

    def get(self, enterprise_id: str) -> dict[str, Any]:
        with self._lock:
            stored = self._read().get(enterprise_id)
            theme = deepcopy(DEFAULT_THEME)
            if stored:
                theme.update(stored)
            theme["enterpriseId"] = enterprise_id
            return theme

    def save(self, enterprise_id: str, theme: dict[str, Any], *, publish: bool = False) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            current = data.get(enterprise_id, {})
            next_version = int(current.get("version", 0)) + 1
            saved = deepcopy(theme)
            saved["version"] = next_version
            saved["status"] = "published" if publish else "draft"
            data[enterprise_id] = saved
            self._write(data)
            saved["enterpriseId"] = enterprise_id
            return saved

    def reset(self, enterprise_id: str) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            data.pop(enterprise_id, None)
            self._write(data)
            return self.get(enterprise_id)
