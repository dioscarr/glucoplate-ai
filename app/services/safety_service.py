from app.schemas.recipe import SafetyReview


class SafetyService:
    disclaimer = (
        "This recipe is for general wellness and meal-planning support only. "
        "It is not medical advice and does not replace guidance from a clinician "
        "or registered dietitian."
    )

    unsafe_terms = [
        "cure diabetes",
        "stop insulin",
        "replace medication",
        "no need for doctor",
        "extreme fasting",
    ]

    def review_text(self, text: str) -> SafetyReview:
        normalized = text.lower()
        warnings = [
            f"Unsafe medical claim detected: {term}"
            for term in self.unsafe_terms
            if term in normalized
        ]

        return SafetyReview(
            approved=not warnings,
            warnings=warnings,
            disclaimer=self.disclaimer,
        )
