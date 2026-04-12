import re
from typing import Any, Dict, List

from llm.structured_output import convert_to_model
from models.budget import BudgetAnalysisResult


class BudgetAgent:
    """
    Validates whether destinations fit the user's budget
    and suggests optimizations if needed.
    """

    def __init__(self):
        self.name = "Budget Optimizer"

    def execute(self, intent_data: dict, destination_data: dict) -> dict:
        if self._should_use_local_outing_budget(intent_data, destination_data):
            return self._build_local_outing_budget(intent_data, destination_data)

        prompt = f"""
USER INTENT:
{intent_data}

DESTINATIONS:
{destination_data}

TASK:
For EACH destination:

1. Estimate total cost breakdown:
   - transport
   - stay
   - food
   - activities

2. Decide feasibility:
   - feasible
   - tight_but_feasible
   - not_feasible

3. Give reasoning:
   - explain cost vs budget mismatch clearly

4. Suggest improvements:
   - cheaper alternatives
   - adjustments

RULES:
- Be realistic (2025 pricing)
- No guessing luxury at low budget
- No vague reasoning
- If trip_scope is local_outing, or origin and destination are the same city:
  - transport means local metro, bus, auto, or short cab rides
  - stay must be INR 0 unless the user explicitly asks for a hotel or overnight stay
  - do NOT include flights or intercity travel
  - for a 1-2 day solo local outing in India, total cost should usually be in the low thousands, not tens of thousands, unless the request is clearly luxury
- If budget_level is unknown:
  - do NOT say "within budget limits"
  - explain that this is an estimate based on reasonable assumptions
- Return pricing_notes with the assumptions used
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=BudgetAnalysisResult
        )

        return result.model_dump()

    def _normalize_location(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _same_location(self, first: str, second: str) -> bool:
        if not first or not second:
            return False
        normalized_first = self._normalize_location(first)
        normalized_second = self._normalize_location(second)
        return (
            normalized_first == normalized_second
            or normalized_first in normalized_second
            or normalized_second in normalized_first
        )

    def _should_use_local_outing_budget(
        self,
        intent_data: Dict[str, Any],
        destination_data: Dict[str, Any],
    ) -> bool:
        if intent_data.get("trip_scope") == "local_outing":
            return True

        origin = intent_data.get("origin", "")
        destination_preference = intent_data.get("destination_preference", "")
        if origin and destination_preference and self._same_location(origin, destination_preference):
            return True

        recommended = destination_data.get("recommended_destinations", [])
        if origin and recommended and self._same_location(origin, recommended[0].get("name", "")):
            return True

        return False

    def _build_local_outing_budget(
        self,
        intent_data: Dict[str, Any],
        destination_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        days = max(1, int(intent_data.get("duration_days", 1)))
        companions = (intent_data.get("companions") or "solo").lower()
        budget_level = (intent_data.get("budget_level") or "unknown").lower()

        companion_factor = {
            "solo": 1.0,
            "couple": 1.8,
            "family": 2.8,
            "friends": 2.2,
            "group": 3.0,
        }.get(companions, 1.5)

        per_day = {
            "low": {"transport": 120, "food": 250, "activities": 300},
            "moderate": {"transport": 180, "food": 400, "activities": 450},
            "high": {"transport": 350, "food": 700, "activities": 900},
            "unknown": {"transport": 150, "food": 350, "activities": 500},
        }.get(budget_level, {"transport": 150, "food": 350, "activities": 500})

        results = []
        for destination in destination_data.get("recommended_destinations", []):
            transport_total = round(per_day["transport"] * days * companion_factor)
            stay_total = 0
            food_total = round(per_day["food"] * days * companion_factor)
            activities_total = round(per_day["activities"] * days * companion_factor)
            total = transport_total + stay_total + food_total + activities_total

            results.append(
                {
                    "destination": f"{destination.get('name', 'Unknown')}, {destination.get('country', 'Unknown')}",
                    "feasibility": "feasible",
                    "estimated_total_cost": f"INR {total:,}",
                    "cost_breakdown": {
                        "transport": f"INR {transport_total:,}",
                        "stay": "INR 0",
                        "food": f"INR {food_total:,}",
                        "activities": f"INR {activities_total:,}",
                    },
                    "reason": (
                        "Estimated as a local outing, not an outstation trip. "
                        "This excludes flights and hotel stay and assumes local transport, casual meals, and a few paid activities."
                    ),
                    "pricing_notes": [
                        "Local outing pricing was used because this request looks like an in-city plan.",
                        "Accommodation was set to INR 0 because no overnight stay or hotel was requested.",
                        (
                            "No explicit budget was provided, so the estimate assumes budget-friendly to moderate local spending."
                            if budget_level == "unknown"
                            else f"The estimate follows the user's {budget_level} budget preference."
                        ),
                    ],
                    "suggested_adjustments": [
                        {
                            "category": "transport",
                            "suggestion": "Use metro plus short auto or cab rides instead of taking cabs everywhere.",
                            "impact": "Keeps local transport cost low."
                        },
                        {
                            "category": "food",
                            "suggestion": "Use local cafes or street food for one meal instead of dining at premium restaurants.",
                            "impact": "Reduces food spend without affecting the outing much."
                        },
                        {
                            "category": "activities",
                            "suggestion": "Mix one paid experience with parks, markets, or low-entry monuments.",
                            "impact": "Keeps the day engaging while controlling costs."
                        },
                    ],
                }
            )

        return {"budget_analysis": results}

    def get_feasible_destinations(self, budget_result: dict) -> List[Dict]:
        """
        Returns destinations that are feasible or tight but feasible.
        """
        return [
            d for d in budget_result.get("budget_analysis", [])
            if d.get("feasibility") in ("feasible", "tight_but_feasible")
        ]

    def get_not_feasible_destinations(self, budget_result: dict) -> List[Dict]:
        """
        Returns destinations that exceed the budget.
        """
        return [
            d for d in budget_result.get("budget_analysis", [])
            if d.get("feasibility") == "not_feasible"
        ]
