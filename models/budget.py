from typing import List, Optional
from pydantic import BaseModel, Field


class BudgetAdjustment(BaseModel):
    category: str = Field(
        ..., description="accommodation | food | activities | transport"
    )
    suggestion: str = Field(
        ..., description="Concrete cost-saving suggestion"
    )
    impact: str = Field(
        ..., description="How this affects the travel experience"
    )


class BudgetItem(BaseModel):
    destination: str = Field(..., description="City, Country")
    feasibility: str = Field(
        ..., description="feasible | not_feasible"
    )
    estimated_total_cost: str = Field(
        ..., description="Estimated trip cost with currency"
    )
    reason: str = Field(
        ..., description="Why it is or is not feasible"
    )
    suggested_adjustments: Optional[List[BudgetAdjustment]] = []


class BudgetAnalysisResult(BaseModel):
    budget_analysis: List[BudgetItem]
