from typing import Any

from app.repositories.json_repository import JsonRepository


class RecipeRepository:
    def __init__(self, json_repository: JsonRepository | None = None) -> None:
        self.json_repository = json_repository or JsonRepository()

    def get_all(self) -> list[dict[str, Any]]:
        return self.json_repository.load_list("recipes.json")

    def search_by_culture_or_goal(self, culture: str | None, goal: str) -> list[dict[str, Any]]:
        recipes = self.get_all()
        goal_lower = goal.lower()
        culture_lower = culture.lower() if culture else None

        matches: list[dict[str, Any]] = []
        for recipe in recipes:
            tags = " ".join(recipe.get("tags", [])).lower()
            title = recipe.get("title", "").lower()
            recipe_culture = recipe.get("culture", "").lower()

            culture_match = culture_lower and culture_lower in recipe_culture
            goal_match = goal_lower in title or any(word in tags for word in goal_lower.split())

            if culture_match or goal_match:
                matches.append(recipe)

        return matches or recipes[:1]
