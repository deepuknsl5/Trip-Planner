from typing import List

from pydantic import BaseModel, Field


class PlanEditIntent(BaseModel):
    is_plan_edit: bool = Field(
        ...,
        description="True when the user is asking to modify the existing trip plan instead of starting a new one",
    )
    summary: str = Field(..., description="Short explanation of the requested modification")
    response_focus: str = Field(
        ...,
        description="itinerary | budget | destination | experiences | full_trip",
    )
    keep_destination: bool = Field(
        True,
        description="Whether the current destination should stay the same",
    )
    requested_changes: List[str] = Field(
        default_factory=list,
        description="Concrete modifications the editor should apply",
    )
