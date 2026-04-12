from datetime import datetime, timedelta
from typing import Dict

from llm.structured_output import convert_to_model
from models.itinerary import ItineraryResult


class ItineraryAgent:
    """
    Creates realistic, human-friendly, day-by-day itineraries
    based on intent + curated experiences.
    """

    def __init__(self):
        self.name = "Itinerary Specialist"
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """
You are a professional travel planner creating REALISTIC itineraries.

CRITICAL RULES (MANDATORY):
- If trip duration <= 7 days, use only ONE destination
- Do NOT include inter-country or long-haul travel inside the itinerary
- Prioritize realistic pacing
- Maximum 3 to 4 activities per day
- Include buffer time, rest, and flexibility
- Respect local meal times and attraction hours
- Use 24-hour time format when specific times are needed
- Output must be valid JSON only
"""

    def _generate_dates(self, days: int) -> Dict[str, str]:
        start = datetime.now().date() + timedelta(days=1)
        return {
            f"Day {i + 1}": (start + timedelta(days=i)).isoformat()
            for i in range(days)
        }

    def execute(self, intent_data: dict, experience_data: dict) -> dict:
        duration = int(intent_data.get("duration_days", 5))
        companions = intent_data.get("companions", "travelers")
        primary_destination = experience_data["experience_plan"][0]["destination"]

        pilgrimage_hint = ""
        if self._is_pilgrimage_destination(primary_destination):
            pilgrimage_hint = f"""
PILGRIMAGE ITINERARY RULES FOR {primary_destination.upper()}:
- Prioritize arrival, check-in, the main shrine visit, practical trek or route planning, meal breaks, rest, recovery, and return planning.
- Avoid generic filler activities that could fit any destination.
- Do not use vague placeholders as if they were real attractions.
- If there are supporting shrine visits or secondary stops, they should come after the main purpose of the pilgrimage, not before it.
- If the trip is short, keep the itinerary centered on the core pilgrimage experience.
"""

        dates = self._generate_dates(duration)

        user_prompt = f"""
TRAVEL INTENT:
{intent_data}

PRIMARY DESTINATION:
{primary_destination}

CURATED EXPERIENCES:
{experience_data}

TRIP DATES:
{dates}

{pilgrimage_hint}

TASK:
Create a {duration}-day itinerary for {companions}.
Ensure realistic timing, logical flow, and practical sequencing.
"""

        itinerary = convert_to_model(
            input_text=user_prompt,
            target_model=ItineraryResult
        )

        itinerary_dict = itinerary.model_dump()

        if self._is_pilgrimage_destination(primary_destination) and self._needs_pilgrimage_review(itinerary_dict):
            review_prompt = f"""
TRAVEL INTENT:
{intent_data}

PRIMARY DESTINATION:
{primary_destination}

CURRENT ITINERARY:
{itinerary_dict}

TASK:
Review and correct this itinerary for realism.

RULES:
- Keep the same destination and trip duration.
- Remove generic filler activities.
- Keep the plan centered on the core pilgrimage purpose.
- Ensure the main shrine visit happens before optional supporting visits.
- Return ONLY corrected JSON matching the schema.
"""
            itinerary = convert_to_model(
                input_text=review_prompt,
                target_model=ItineraryResult
            )
            itinerary_dict = itinerary.model_dump()

        return itinerary_dict

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

    def _needs_pilgrimage_review(self, itinerary: dict) -> bool:
        generic_terms = [
            "stargazing",
            "nightlife",
            "cuisine exploration",
            "heritage walk",
            "shopping",
            "picnic",
        ]

        text_parts = []
        for day in itinerary.get("itinerary", []):
            for item in day.get("plan", []):
                text_parts.append(item.get("activity", ""))
                text_parts.append(item.get("notes", ""))

        combined = " ".join(text_parts).lower()
        return any(term in combined for term in generic_terms)
