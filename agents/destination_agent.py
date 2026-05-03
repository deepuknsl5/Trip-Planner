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
Recommend EXACTLY 3 travel destinations.

CONSTRAINTS (STRICT):
- If user specifies a destination_preference → stay within that region
- If country_preference is given → do not go outside that country
- If duration ≤ 3–5 days → suggest geographically nearby and realistic locations
- If origin is given → prefer destinations reachable within reasonable travel time

QUALITY RULES:
- Do NOT override user intent
- Do NOT suggest unrelated or far-away places
- Avoid mixing regions (e.g., Himachal + South India)
- Be geographically consistent
- Do NOT invent obscure micro-locations to sound smart
- If uncertain, prefer well-known city or region names over overly specific local claims

OUTPUT REQUIREMENTS:
Each destination must include:
- name
- country
- why_suitable
- best_for
- budget_range
- ideal_duration
- best_season
- pros
- cons
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=DestinationRecommendation
        )

        result_dict = result.model_dump()

        destination_pref = intent_data.get("destination_preference", "")
        country_pref = intent_data.get("country_preference", "")

        filtered = []

        for d in result_dict["recommended_destinations"]:
            name = d["name"].lower()
            country = d["country"].lower()

            # ✅ Country constraint
            if country_pref and country_pref.lower() not in country:
                continue

            # ✅ Destination preference (soft match)
            if destination_pref:
                if destination_pref.lower() not in name:
                    # allow partial mismatch but penalize later
                    pass

            filtered.append(d)

        # fallback if everything filtered out
        if filtered:
            result_dict["recommended_destinations"] = filtered[:3]
        return result_dict
