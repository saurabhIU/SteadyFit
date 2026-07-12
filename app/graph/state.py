"""Shared state for the OneRepMax coaching council graph."""
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class WorkoutDay(BaseModel):
    day: str                     # "Mon"
    focus: str                   # "Upper push"
    duration_min: int = 45
    status: Literal["planned", "done", "skipped", "moved"] = "planned"


class WeekPlan(BaseModel):
    week_start: str              # ISO date
    days: list[WorkoutDay] = []
    calorie_target: int = 2200
    protein_target_g: int = 150
    notes: str = ""


class UserProfile(BaseModel):
    name: str = "athlete"
    goal: str = "general fitness"        # e.g. "lose 8kg by November"
    sessions_per_week: int = 3
    injuries: list[str] = []
    food_preferences: list[str] = []
    workout_preferences: list[str] = []


class CouncilState(BaseModel):
    """State object every agent node reads and writes."""
    messages: Annotated[list, add_messages] = []
    profile: UserProfile = UserProfile()
    week_plan: Optional[WeekPlan] = None
    intent: Optional[str] = None          # set by coach: schedule|nutrition|adherence|knowledge
    proposals: dict = Field(default_factory=dict)   # specialist -> proposal text/json
    risk_flag: bool = False               # set by adherence agent
    council_rounds: int = 0               # guard against infinite negotiation loops
    retrieved_context: list[str] = []     # RAG chunks / search results with source tags
