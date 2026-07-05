from app.ai.agents.base_agent import BaseAgent


class NutritionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_name="nutrition", prompt_file="nutrition.md")
