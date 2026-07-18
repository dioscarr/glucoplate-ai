from __future__ import annotations

import re
from typing import Any


class PantryCoverageService:
    """Classify recipe ingredients against structured pantry context."""

    OPTIONAL_MARKERS = {"optional", "to serve", "for garnish", "garnish"}

    @staticmethod
    def _tokens(value: Any) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
            if len(token) > 2
        }

    def analyze(
        self,
        ingredients: list[str],
        pantry_items: list[str] | None = None,
        use_soon_ingredients: list[str] | None = None,
    ) -> dict[str, Any]:
        pantry = [str(item).strip() for item in pantry_items or [] if str(item).strip()]
        use_soon = [str(item).strip() for item in use_soon_ingredients or [] if str(item).strip()]
        pantry_tokens = [(item, self._tokens(item)) for item in pantry]
        use_soon_tokens = [(item, self._tokens(item)) for item in use_soon]

        already_have: list[str] = []
        need_to_buy: list[str] = []
        optional: list[str] = []
        use_soon_matches: list[str] = []

        for ingredient in ingredients:
            text = str(ingredient).strip()
            tokens = self._tokens(text)
            if any(marker in text.lower() for marker in self.OPTIONAL_MARKERS):
                optional.append(text)
                continue

            matched = [name for name, item_tokens in pantry_tokens if tokens & item_tokens]
            if matched:
                already_have.append(text)
                if any(tokens & item_tokens for _, item_tokens in use_soon_tokens):
                    use_soon_matches.append(text)
            else:
                need_to_buy.append(text)

        required_count = len(already_have) + len(need_to_buy)
        coverage_ratio = round(len(already_have) / required_count, 4) if required_count else 0
        coverage_percent = round(coverage_ratio * 100)
        return {
            "already_have": already_have,
            "need_to_buy": need_to_buy,
            "optional": optional,
            "use_soon_matches": use_soon_matches,
            "pantry_coverage": {
                "available_count": len(already_have),
                "required_count": required_count,
                "coverage_ratio": coverage_ratio,
                "coverage_percent": coverage_percent,
            },
        }
