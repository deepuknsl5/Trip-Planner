from pydantic import BaseModel
from typing import List, Optional

class TravelIntent(BaseModel):
    travel_purpose: str
    travel_type: str
    budget_level: str
    duration_days: int
    companions: str
    special_preferences: List[str] = []
