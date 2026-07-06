from pathlib import Path

from app.ai.copilot_agent_client import CopilotAgentClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = PROJECT_ROOT / "prompts"


class BaseAgent:
    def __init__(self, agent_name: str, prompt_file: str, client: CopilotAgentClient | None = None) -> None:
        self.agent_name = agent_name
        self.prompt_file = prompt_file
        self.client = client or CopilotAgentClient()

    def load_prompt_template(self) -> str:
        path = PROMPTS_DIR / self.prompt_file
        return path.read_text(encoding="utf-8")

    async def run(self, context: str) -> str:
        template = self.load_prompt_template()
        prompt = template.replace("{{context}}", context)
        return await self.client.ask(prompt)
