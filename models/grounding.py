from typing import List

from pydantic import BaseModel, Field


class GroundingReport(BaseModel):
    safe_to_return: bool = Field(
        ...,
        description="True if the plan avoids unsupported or invented factual details",
    )
    avoids_invented_specifics: bool = Field(
        ...,
        description="True if the plan avoids ungrounded venue names, ratings, hours, or other precise claims",
    )
    consistent_across_sections: bool = Field(
        ...,
        description="True if destinations, budget, experiences, and itinerary do not contradict each other",
    )
    uses_estimates_not_fake_precision: bool = Field(
        ...,
        description="True if travel times and costs are presented as reasonable estimates rather than false certainty",
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Short descriptions of hallucination or grounding risks",
    )
    revision_required: bool = Field(
        ...,
        description="True if the plan should be revised before returning to the user",
    )
    revision_instructions: List[str] = Field(
        default_factory=list,
        description="Concrete fixes to remove hallucination risk",
    )
