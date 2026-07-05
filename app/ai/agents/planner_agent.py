from app.ai.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_name="planner", prompt_file="planner.md")
