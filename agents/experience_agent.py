# # agents/experience_agent.py

# from llm.openai_client import call_openai


# class ExperienceAgent:
#     """
#     ExperienceAgent curates personalized activities
#     for feasible destinations.
#     """

#     def __init__(self):
#         self.system_prompt = """
# You are a travel experience curator.

# Input:
# - Travel intent JSON
# - Budget feasibility analysis

# Your task:
# - Suggest meaningful experiences for each feasible destination
# - Experiences must match travel purpose, companions, and preferences
# - Avoid generic or unrealistic activities

# Return ONLY valid JSON in this format:
# {
#   "experience_plan": [
#     {
#       "destination": "",
#       "experiences": [
#         {
#           "title": "",
#           "description": "",
#           "experience_type": ""
#         }
#       ]
#     }
#   ]
# }

# Rules:
# - No markdown
# - No explanations outside JSON
# - Be specific and practical
# """
    
#     def execute(self, intent_data: dict, budget_data: dict) -> dict:
#         """
#         Executes ExperienceAgent using intent and budget analysis.
#         """

#         user_prompt = f"""
# Travel Intent:
# {intent_data}

# Budget Analysis:
# {budget_data}

# Only consider destinations marked as feasible.
# Suggest experiences accordingly.
# """

#         response = call_openai(
#             system_prompt=self.system_prompt,
#             user_prompt=user_prompt,
#             temperature=0.35
#         )

#         return response
from llm.structured_output import convert_to_model
from models.experience import ExperiencePlanResult


class ExperienceAgent:
    """
    Curates meaningful experiences ONLY for budget-feasible destinations.
    """

    def __init__(self):
        self.name = "Experience Curator"

    def execute(self, intent_data: dict, budget_data: dict) -> dict:
        prompt = f"""
TRAVEL INTENT:
{intent_data}

BUDGET ANALYSIS:
{budget_data}

TASK:
ONLY for destinations marked as feasible:
- Create signature experiences
- Add cultural / food experiences
- Add free or relaxing activities
- Include insider tips

RULES:
- No tourist traps
- Mix budget & premium experiences
- Match companions and travel purpose
"""

        result = convert_to_model(
            input_text=prompt,
            target_model=ExperiencePlanResult
        )

        return result.model_dump()
