from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TripOption(BaseModel):
    label: Literal["Plan A", "Plan B"] = Field(..., description="Plan A or Plan B")
    summary: str = Field(..., description="Short summary of the trip version")
    best_for: str = Field(..., description="Who this option is best suited for")
    tradeoff: str = Field(..., description="Main tradeoff compared with the other option")
    estimated_total_cost: str = Field(..., description="Approximate trip cost with currency")


class ItineraryStop(BaseModel):
    start_time: str = Field(..., description="Start time in 24-hour HH:MM format")
    end_time: str = Field(..., description="End time in 24-hour HH:MM format")
    place: str = Field(..., description="Specific venue, landmark, or neighborhood")
    activity: str = Field(..., description="What the traveler will do at this stop")
    category: str = Field(
        ...,
        description="meal | sightseeing | transfer | rest | check_in | culture | outdoor | shopping | pilgrimage | nightlife",
    )
    transit_mode_from_previous: Optional[str] = Field(
        None,
        description="walk | cab | metro | auto | bus | ferry | train | shuttle | self_drive | none",
    )
    transit_time_from_previous_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Travel time from the previous stop in minutes",
    )
    buffer_minutes: int = Field(
        0,
        ge=0,
        description="Extra buffer added for queues, traffic, or transitions",
    )
    estimated_cost: str = Field(..., description="Approximate cost for this stop with currency")
    reason_to_visit: str = Field(..., description="Why this stop improves the trip")
    notes: str = Field(..., description="Practical notes such as booking, crowds, or pacing")
    backup_option: str = Field(
        ...,
        description="Fallback option if weather, queues, or fatigue affect this stop",
    )


class DayPlan(BaseModel):
    day: str = Field(..., description="Day label such as Day 1")
    date: str = Field(..., description="ISO date for this day")
    zone: str = Field(..., description="Main area or cluster covered that day")
    theme: str = Field(..., description="Short description of the day's focus")
    start_time: str = Field(..., description="Day start in 24-hour HH:MM format")
    end_time: str = Field(..., description="Day end in 24-hour HH:MM format")
    estimated_day_cost: str = Field(..., description="Approximate daily spend with currency")
    local_transport_strategy: str = Field(
        ...,
        description="How to move between stops efficiently that day",
    )
    plan: List[ItineraryStop] = Field(..., description="Ordered stops for the day")


class ItineraryResult(BaseModel):
    trip_style: str = Field(..., description="Overall pacing and travel style for the trip")
    planning_logic: str = Field(..., description="Why the route and sequencing make sense")
    internal_transport_tip: str = Field(
        ...,
        description="Best practical guidance for moving around the destination",
    )
    trip_options: List[TripOption] = Field(
        ...,
        description="Exactly two options labelled Plan A and Plan B",
        min_length=2,
        max_length=2,
    )
    itinerary: List[DayPlan] = Field(..., description="Primary day-by-day trip plan")
