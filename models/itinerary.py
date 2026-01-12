from pydantic import BaseModel
from typing import List

class TimeSlot(BaseModel):
    time_slot: str
    activity: str
    notes: str


class DayPlan(BaseModel):
    day: str
    plan: List[TimeSlot]


class ItineraryResult(BaseModel):
    itinerary: List[DayPlan]
