from pydantic import BaseModel
from typing import List, Optional


class TravelIntent(BaseModel):
    travel_purpose: str
    travel_type: str
    budget_level: str
    duration_days: int
    companions: str

    # 🔥 NEW FIELDS
    origin: Optional[str] = None
    destination_preference: Optional[str] = None
    country_preference: Optional[str] = None

    special_preferences: List[str] = []