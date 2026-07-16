from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class EnterpriseAuthService:
    def __init__(self, companies_path: Path | None = None) -> None:
        self.companies_path = companies_path or Path(__file__).resolve().parents[1] / "data" / "companies.json"

    @lru_cache(maxsize=1)
    def _companies(self) -> tuple[dict[str, Any], ...]:
        payload = json.loads(self.companies_path.read_text(encoding="utf-8"))
        return tuple(payload.get("companies", []))

    def validate_access_code(self, access_code: str) -> dict[str, Any] | None:
        normalized = access_code.strip()
        for company in self._companies():
            if company.get("active") and str(company.get("access_code", "")) == normalized:
                return {
                    "id": company["id"],
                    "name": company["name"],
                    "role": company.get("role", "member"),
                }
        return None
