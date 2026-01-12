# agents/destination_agent.py

# from llm.openai_client import call_openai


# class DestinationAgent:
#     """
#     DestinationAgent suggests suitable travel destinations
#     based on structured travel intent.
#     """

#     def __init__(self):
#         self.system_prompt = """
# You are an expert travel destination advisor.

# Input:
# You will receive structured travel intent as JSON.

# Your task:
# - Suggest 3 realistic travel destinations
# - Destinations must match intent, budget, duration, and season
# - Avoid luxury destinations if budget is low
# - Avoid vague suggestions

# Return ONLY valid JSON in this format:
# {
#   "recommended_destinations": [
#     {
#       "name": "",
#       "country": "",
#       "why_suitable": ""
#     }
#   ]
# }

# Rules:
# - No markdown
# - No explanations outside JSON
# - Be realistic and practical
# """
    
#     def execute(self, intent_data: dict) -> dict:
#         """
#         Executes the DestinationAgent using intent data.
#         """

#         user_prompt = f"""
# Travel Intent:
# {intent_data}

# Suggest destinations based on the above intent.
# """

#         response = call_openai(
#             system_prompt=self.system_prompt,
#             user_prompt=user_prompt,
#             temperature=0.3
#         )

#         return response
from llm.structured_output import convert_to_model
from models.destination import DestinationRecommendation


class DestinationAgent:
    """
    Suggests realistic travel destinations based on user intent.
    """

    def __init__(self):
        self.name = "Destination Explorer"

    def execute(self, intent_data: dict) -> dict:
        prompt = f"""
TRAVEL INTENT:
{intent_data}

TASK:
Recommend exactly 3 realistic travel destinations that fit the intent.
Consider budget, duration, travel purpose, and companions.

RULES:
- Use city + country
- Be mainstream and tourist-friendly
- Avoid vague regions
- Be honest about pros and cons
"""

        result = convert_to_model(
            input_text=prompt,
            target_model=DestinationRecommendation
        )

        return result.model_dump()
