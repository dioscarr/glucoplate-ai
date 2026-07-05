from app.ai.agents.base_agent import BaseAgent


class RecipeAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_name="recipe", prompt_file="recipe.md")
