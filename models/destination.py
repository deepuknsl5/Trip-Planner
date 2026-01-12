from typing import List
from pydantic import BaseModel, Field


class DestinationItem(BaseModel):
    name: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    why_suitable: str = Field(..., description="Why this destination fits the user")
    best_for: List[str] = Field(..., description="Interests this destination suits")
    budget_range: str = Field(..., description="low | medium | high")
    ideal_duration: str = Field(..., description="Ideal trip length")
    best_season: str = Field(..., description="Best time to visit")
    pros: List[str]
    cons: List[str]


class DestinationRecommendation(BaseModel):
    recommended_destinations: List[DestinationItem]
