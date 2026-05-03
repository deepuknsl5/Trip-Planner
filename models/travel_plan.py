from typing import List

from pydantic import BaseModel, Field

from models.budget import BudgetAnalysisResult, BudgetItem
from models.destination import DestinationRecommendation
from models.experience import ExperiencePlanResult
from models.intent import TravelIntent
from models.itinerary import ItineraryResult


class EditableTravelPlan(BaseModel):
    intent: TravelIntent
    assumptions: List[str] = Field(default_factory=list)
    destinations: DestinationRecommendation
    budget_analysis: BudgetAnalysisResult
    feasible_destinations: List[BudgetItem] = Field(default_factory=list)
    experiences: ExperiencePlanResult
    itinerary: ItineraryResult
    planner_brief: str
