from typing import List

from pydantic import BaseModel, Field


class PlanQualityReport(BaseModel):
    saves_time: bool = Field(
        ...,
        description="True if the output clearly reduces planning work for the user",
    )
    works_in_real_world: bool = Field(
        ...,
        description="True if the route, budget, pacing, and timings look practical",
    )
    feels_personalized: bool = Field(
        ...,
        description="True if the plan clearly reflects the user's destination, budget, group, and preferences",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Short points describing what already works well",
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Short points describing what is weak or generic",
    )
    revision_required: bool = Field(
        ...,
        description="True if the plan should be revised before returning to the user",
    )
    revision_instructions: List[str] = Field(
        default_factory=list,
        description="Concrete instructions for revising the plan",
    )
