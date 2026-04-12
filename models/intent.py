import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TravelIntent(BaseModel):
    is_travel_request: bool = True
    travel_purpose: str = "trip"
    travel_type: str = "plan"
    budget_level: str = "unknown"
    trip_scope: str = "trip"
    response_focus: str = "full_trip"
    duration_days: int = 3
    companions: str = "solo"
    origin: Optional[str] = None
    destination_preference: Optional[str] = None
    country_preference: Optional[str] = None
    special_preferences: List[str] = Field(default_factory=list)

    @field_validator(
        "travel_purpose",
        "travel_type",
        "budget_level",
        "trip_scope",
        "response_focus",
        "companions",
        mode="before",
    )
    @classmethod
    def fill_missing_strings(cls, value, info):
        defaults = {
            "travel_purpose": "trip",
            "travel_type": "plan",
            "budget_level": "unknown",
            "trip_scope": "trip",
            "response_focus": "full_trip",
            "companions": "solo",
        }

        if value is None:
            return defaults[info.field_name]

        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or defaults[info.field_name]

        return str(value)

    @field_validator("duration_days", mode="before")
    @classmethod
    def fill_missing_duration(cls, value, info):
        if value is None or value == "":
            trip_scope = str(info.data.get("trip_scope", "trip")).lower()
            return 2 if trip_scope == "local_outing" else 3

        if isinstance(value, str):
            cleaned = value.strip().lower()
            if not cleaned:
                trip_scope = str(info.data.get("trip_scope", "trip")).lower()
                return 2 if trip_scope == "local_outing" else 3

            if "weekend" in cleaned:
                return 2

            match = re.search(r"\d+", cleaned)
            if match:
                return int(match.group())

        return value
