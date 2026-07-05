from app.ai.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_name="reviewer", prompt_file="reviewer.md")
