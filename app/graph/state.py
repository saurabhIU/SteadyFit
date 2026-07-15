"""Shared state for the SteadyFit AI Coaching Team graph."""
from typing import Annotated, Literal, Optional

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

WorkoutMode = Literal["gym", "swimming", "walking", "running", "home", "cycling", "yoga"]
FoodPreference = Literal[
    "vegetarian", "non-vegetarian", "vegan", "eggetarian", "no-preference"
]
WORKOUT_MODE_OPTIONS: list[str] = [
    "gym", "swimming", "walking", "running", "home", "cycling", "yoga",
]
FOOD_PREFERENCE_OPTIONS: list[str] = [
    "vegetarian", "non-vegetarian", "vegan", "eggetarian", "no-preference",
]


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
    # Empty until intake fills it — "general fitness" is no longer a fake default.
    goal: str = ""
    age: int | None = None
    age_declined: bool = False
    sex: str | None = None  # male | female | other | prefer_not_to_say
    sex_declined: bool = False
    preferred_workout_modes: list[str] = Field(default_factory=list)
    food_preference: str | None = None
    sessions_per_week: int | None = None
    constraints: list[str] = Field(default_factory=list)
    constraints_asked: bool = False
    onboarding_complete: bool = False
    # Required slots filled; awaiting "looks good" before first WeekPlan.
    awaiting_onboarding_confirm: bool = False

    # Backward-compatible aliases used by older agents / UI.
    @property
    def injuries(self) -> list[str]:
        return list(self.constraints)

    @property
    def food_preferences(self) -> list[str]:
        return [self.food_preference] if self.food_preference else []

    @property
    def workout_preferences(self) -> list[str]:
        return list(self.preferred_workout_modes)


class CoachingTeamState(BaseModel):
    """State object every agent node reads and writes."""
    messages: Annotated[list, add_messages] = []
    profile: UserProfile = Field(default_factory=UserProfile)
    week_plan: Optional[WeekPlan] = None
    intent: Optional[str] = None
    # schedule|nutrition|adherence|knowledge|intake|first_plan
    proposals: dict = Field(default_factory=dict)
    risk_flag: bool = False
    coaching_team_rounds: int = 0
    retrieved_context: list[str] = []
    # UI chips for the latest intake question
    quick_replies: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
