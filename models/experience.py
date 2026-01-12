from typing import List, Optional
from pydantic import BaseModel, Field


class SignatureExperience(BaseModel):
    title: str
    category: str
    description: str
    why_special: str
    duration: str
    best_time: str
    budget_category: str
    approximate_cost: str
    insider_tips: List[str]


class AdditionalExperience(BaseModel):
    title: str
    description: str
    duration: str
    cost: str
    insider_tips: List[str]


class FreeActivity(BaseModel):
    title: str
    best_time: str
    insider_tips: List[str]


class DestinationExperiencePlan(BaseModel):
    destination: str
    signature_experiences: List[SignatureExperience]
    additional_experiences: List[AdditionalExperience]
    free_activities: List[FreeActivity]


class ExperiencePlanResult(BaseModel):
    experience_plan: List[DestinationExperiencePlan]

