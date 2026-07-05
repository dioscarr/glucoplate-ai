from app.ai.agents.base_agent import BaseAgent


class SafetyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_name="safety", prompt_file="safety.md")
