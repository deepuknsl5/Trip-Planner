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


class CostBreakdown(BaseModel):
    transport: str = Field(..., description="Local transport or travel cost")
    stay: str = Field(..., description="Accommodation cost")
    food: str = Field(..., description="Food and drinks cost")
    activities: str = Field(..., description="Paid experiences and entry fees")


class BudgetItem(BaseModel):
    destination: str = Field(..., description="City, Country")
    feasibility: str = Field(
        ..., description="feasible | tight_but_feasible | not_feasible"
    )
    estimated_total_cost: str = Field(
        ..., description="Estimated trip cost with currency"
    )
    cost_breakdown: Optional[CostBreakdown] = None
    reason: str = Field(
        ..., description="Why it is or is not feasible"
    )
    pricing_notes: Optional[List[str]] = []
    suggested_adjustments: Optional[List[BudgetAdjustment]] = []


class BudgetAnalysisResult(BaseModel):
    budget_analysis: List[BudgetItem]
