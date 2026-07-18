from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


class RecipeRecommendationService:
    """Rank recipe concepts with transparent Flavor Memory signals."""

    WEIGHTS = {"saved": 5, "cooked": 10, "repeated": 20, "dismissed": -8}

    @staticmethod
    def _tokens(*values: Any) -> set[str]:
        text = " ".join(str(value or "") for value in values).lower()
        return {token for token in re.findall(r"[a-z0-9]+", text) if len(token) > 2}

    def build_candidates(self, goal: str, culture: str | None = None) -> list[dict[str, Any]]:
        subject = " ".join(str(goal or "Dinner").split()).strip() or "Dinner"
        subject = subject[:100]
        culture_name = " ".join(str(culture or "").split()).strip()
        return [
            {
                "id": "familiar",
                "title": f"Classic {subject}",
                "direction": "A familiar, dependable version focused on comfort and straightforward technique.",
                "cuisine": culture_name or None,
                "tags": ["classic", "comfort", "family-friendly"],
            },
            {
                "id": "fast",
                "title": f"Quick {subject}",
                "direction": "A faster weeknight version with fewer steps and practical substitutions.",
                "cuisine": culture_name or None,
                "tags": ["quick", "easy", "weeknight"],
            },
            {
                "id": "fresh",
                "title": f"Fresh Twist on {subject}",
                "direction": "A distinct variation that keeps the request recognizable while adding contrast and freshness.",
                "cuisine": culture_name or None,
                "tags": ["fresh", "creative", "balanced"],
            },
            {
                "id": "one-pan",
                "title": f"One-Pan {subject}",
                "direction": "A low-cleanup direction designed around one primary pan or pot.",
                "cuisine": culture_name or None,
                "tags": ["one-pan", "easy", "low-cleanup"],
            },
            {
                "id": "protein-forward",
                "title": f"Protein-Forward {subject}",
                "direction": "A satisfying direction that emphasizes protein and balanced portions.",
                "cuisine": culture_name or None,
                "tags": ["protein", "balanced", "satisfying"],
            },
        ]

    def rank(
        self,
        goal: str,
        interactions: list[dict[str, Any]],
        preferences: dict[str, Any] | None = None,
        candidates: list[dict[str, Any]] | None = None,
        culture: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        pool = list(candidates or self.build_candidates(goal, culture))
        preference_tokens = self._tokens(preferences or {})
        history = []
        for item in interactions:
            history.append((
                self._tokens(item.get("recipe_name"), item.get("cuisine"), item.get("tags")),
                self.WEIGHTS.get(str(item.get("interaction_type") or "").lower(), 0),
                str(item.get("interaction_type") or "").lower(),
            ))

        ranked = []
        for index, candidate in enumerate(pool):
            candidate_tokens = self._tokens(candidate.get("title"), candidate.get("direction"), candidate.get("cuisine"), candidate.get("tags"))
            score = 0
            reasons: list[str] = []
            signal_totals: dict[str, int] = defaultdict(int)

            for history_tokens, weight, signal in history:
                overlap = candidate_tokens & history_tokens
                if overlap:
                    contribution = weight * min(len(overlap), 3)
                    score += contribution
                    signal_totals[signal] += contribution

            preference_overlap = candidate_tokens & preference_tokens
            if preference_overlap:
                score += 4 * min(len(preference_overlap), 3)
                reasons.append("Matches preferences saved for this profile")

            if signal_totals.get("repeated", 0) > 0:
                reasons.append("Similar to meals you choose again")
            elif signal_totals.get("cooked", 0) > 0:
                reasons.append("Similar to recipes you have completed")
            elif signal_totals.get("saved", 0) > 0:
                reasons.append("Similar to recipes you have saved")
            if signal_totals.get("dismissed", 0) < 0:
                reasons.append("Reduced because similar ideas were skipped")
            if not reasons:
                reasons.append("Provides a distinct direction for your request")

            ranked.append({**candidate, "score": score, "why_this_fits": reasons[:2], "_order": index})

        ranked.sort(key=lambda item: (-item["score"], item["_order"]))
        selected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in ranked:
            identity = str(item.get("id") or item.get("title") or "").lower()
            if not identity or identity in seen_ids:
                continue
            seen_ids.add(identity)
            selected.append({key: value for key, value in item.items() if key != "_order"})
            if len(selected) >= max(1, min(limit, 5)):
                break
        return selected
