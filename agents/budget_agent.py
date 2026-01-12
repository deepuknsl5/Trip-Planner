# from llm.openai_client import call_openai

# class BudgetAgent:
#     """
#     BudgetAgent validates and optimizes destinations
#     based on user's budget and duration.
#     """

#     def __init__(self):
#         self.system_prompt = """
# You are a travel budget analyst.

# Input:
# - Travel intent JSON
# - List of recommended destinations

# Your task:
# - Evaluate budget feasibility for each destination
# - Mark each destination as "feasible" or "not_feasible"
# - If not feasible, explain briefly why
# - Suggest cost-saving adjustments if needed

# Return ONLY valid JSON in this format:
# {
#   "budget_analysis": [
#     {
#       "destination": "",
#       "feasibility": "",
#       "reason": "",
#       "suggested_adjustments": []
#     }
#   ]
# }

# Rules:
# - No markdown
# - No extra explanation
# - Be realistic with costs
# """
    
#     def execute(self, intent_data: dict, destination_data: dict) -> dict:
#         """
#         Executes BudgetAgent using intent and destination data.
#         """

#         user_prompt = f"""
# Travel Intent:
# {intent_data}

# Recommended Destinations:
# {destination_data}

# Analyze budget feasibility.
# """

#         response = call_openai(
#             system_prompt=self.system_prompt,
#             user_prompt=user_prompt,
#             temperature=0.25
#         )

#         return response
from llm.structured_output import convert_to_model
from models.budget import BudgetAnalysisResult
from typing import List, Dict


class BudgetAgent:
    """
    Validates whether destinations fit the user's budget
    and suggests optimizations if needed.
    """

    def __init__(self):
        self.name = "Budget Optimizer"

    def execute(self, intent_data: dict, destination_data: dict) -> dict:
        prompt = f"""
USER BUDGET & TRAVEL INTENT:
{intent_data}

DESTINATIONS TO ANALYZE:
{destination_data}

TASK:
For EACH destination:
- Estimate realistic total trip cost
- Decide feasibility (feasible / not_feasible / tight_but_feasible)
- Explain reasoning
- Suggest cost-saving adjustments if needed

RULES:
- Use conservative 2025 pricing
- Be honest (no luxury on moderate budgets)
- Do not hallucinate deals
"""

        result = convert_to_model(
            input_text=prompt,
            target_model=BudgetAnalysisResult
        )

        return result.model_dump()

    # -------------------------------------------------
    # Helper methods (USED BY COORDINATOR)
    # -------------------------------------------------

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
