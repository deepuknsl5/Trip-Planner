from llm.structured_output import convert_to_model
from models.experience import ExperiencePlanResult


class ExperienceAgent:
    """
    Curates meaningful experiences ONLY for budget-feasible destinations.
    """

    def __init__(self):
        self.name = "Experience Curator"

    def execute(self, intent_data: dict, budget_data: dict) -> dict:
        destination_name = self._get_primary_destination_name(budget_data, intent_data)
        pilgrimage_hint = ""

        if self._is_pilgrimage_destination(destination_name):
            pilgrimage_hint = f"""
PILGRIMAGE DESTINATION RULES FOR {destination_name.upper()}:
- Prioritize shrine access, darshan, trek logistics, queue management, rest windows, meal breaks, arrival/departure practicality, and nearby pilgrimage-relevant stops.
- Avoid generic filler that could fit almost any destination.
- Do not invent nightlife, random heritage walks, stargazing, shopping, or broad cuisine exploration unless the user explicitly asked for those.
- Supporting experiences must feel necessary and locally relevant to the pilgrimage trip.
"""

        prompt = f"""
TRAVEL INTENT:
{intent_data}

BUDGET ANALYSIS:
{budget_data}

IMPORTANT:
- If only ONE destination, generate the full experience plan for that location
- Do NOT assume multiple destinations
{pilgrimage_hint}

TASK:
Generate detailed experiences for the given destination(s)
"""

        result = convert_to_model(
            input_text=prompt,
            target_model=ExperiencePlanResult
        )

        if self._is_pilgrimage_destination(destination_name) and self._needs_pilgrimage_review(result.model_dump()):
            review_prompt = f"""
TRAVEL INTENT:
{intent_data}

PRIMARY DESTINATION:
{destination_name}

CURRENT EXPERIENCE PLAN:
{result.model_dump()}

TASK:
Review and correct the experience plan for a pilgrimage-focused trip.

RULES:
- Keep the same destination and overall trip scope.
- Remove generic filler experiences.
- Keep only realistic, pilgrimage-relevant experiences and supporting activities.
- Return ONLY corrected JSON matching the schema.
"""
            result = convert_to_model(
                input_text=review_prompt,
                target_model=ExperiencePlanResult
            )

        if not result.experience_plan:
            raise ValueError("No experiences generated")
        return result.model_dump()

    def _get_primary_destination_name(self, budget_data: dict, intent_data: dict) -> str:
        if intent_data.get("destination_preference"):
            return str(intent_data["destination_preference"])

        budget_items = budget_data.get("budget_analysis", [])
        if budget_items:
            return str(budget_items[0].get("destination", ""))
        return ""

    def _is_pilgrimage_destination(self, destination_name: str) -> bool:
        normalized = destination_name.lower()
        return any(
            token in normalized
            for token in [
                "vaishno devi",
                "vaishnodevi",
                "tirupati",
                "kedarnath",
                "badrinath",
                "amarnath",
                "somnath",
                "haridwar",
                "rishikesh",
            ]
        )

    def _needs_pilgrimage_review(self, result: dict) -> bool:
        generic_terms = [
            "stargazing",
            "nightlife",
            "cuisine exploration",
            "heritage walk",
            "shopping",
            "picnic",
        ]

        text_parts = []
        for plan in result.get("experience_plan", []):
            for item in plan.get("signature_experiences", []):
                text_parts.append(item.get("title", ""))
                text_parts.append(item.get("description", ""))
            for item in plan.get("additional_experiences", []):
                text_parts.append(item.get("title", ""))
                text_parts.append(item.get("description", ""))
            for item in plan.get("free_activities", []):
                text_parts.append(item.get("title", ""))

        combined = " ".join(text_parts).lower()
        return any(term in combined for term in generic_terms)
