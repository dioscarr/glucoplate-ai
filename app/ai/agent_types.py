from enum import StrEnum
from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    PLANNER = "planner"
    RECIPE = "recipe"
    NUTRITION = "nutrition"
    SAFETY = "safety"
    REVIEWER = "reviewer"


class AgentMessage(BaseModel):
    role: AgentRole
    prompt: str
    output: str | None = None


class RecipePlan(BaseModel):
    user_goal: str
    strategy: str
    target_carb_range: str
    required_sections: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
