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
- Use 24-hour time format for every stop and every day summary
- Include travel time between consecutive stops
- Keep nearby places together so the route feels geographically usable
- Add estimated cost at stop level and day level
- Return EXACTLY two trip options labelled Plan A and Plan B
- Plan A should be the balanced first-choice itinerary
- Plan B should be a practical alternative with a clear tradeoff such as lower cost, lighter pace, or better weather backup
- If you are unsure about a specific attraction detail, use a precise area-level stop instead of inventing facts
- The user should feel: "This saved me time", "This plan actually works", and "It feels personalized"
- Do NOT invent exact restaurant, cafe, hotel, shop, or niche venue names just to make the plan look detailed
- Do NOT claim live opening hours, ratings, or real-time queue conditions
- Present travel time and cost as practical estimates, not guaranteed facts
- Output must be valid JSON only
"""

    def _generate_dates(self, days: int) -> Dict[str, str]:
        start = datetime.now().date() + timedelta(days=1)
        return {
            f"Day {i + 1}": (start + timedelta(days=i)).isoformat()
            for i in range(days)
        }

    def execute(self, intent_data: dict, experience_data: dict, budget_data: dict) -> dict:
        duration = int(intent_data.get("duration_days", 5))
        companions = intent_data.get("companions", "travelers")
        primary_destination = self._get_primary_destination(intent_data, experience_data, budget_data)

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
SYSTEM RULES:
{self.system_prompt}

TRAVEL INTENT:
{intent_data}

PRIMARY DESTINATION:
{primary_destination}

CURATED EXPERIENCES:
{experience_data}

BUDGET CONTEXT:
{budget_data}

TRIP DATES:
{dates}

{pilgrimage_hint}

TASK:
Create a {duration}-day itinerary for {companions}.
Ensure realistic timing, logical flow, and practical sequencing.
The output must feel usable, not generic:
- Include exact start and end times for every stop
- Include transit mode and transit time from the previous stop
- Add buffer minutes for queues, traffic, and check-ins
- Include estimated cost for each stop and each day
- Use Plan A and Plan B so the user gets a main version plus a fallback
- Make the sequencing feel decision-ready so the user does not need to do major extra planning
- Reflect the user's constraints and preferences explicitly in route choices and pacing
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
- Keep exact timings, transit information, buffers, and Plan A / Plan B intact.
- Return ONLY corrected JSON matching the schema.
"""
            itinerary = convert_to_model(
                input_text=review_prompt,
                target_model=ItineraryResult
            )
            itinerary_dict = itinerary.model_dump()

        return itinerary_dict

    def _get_primary_destination(
        self,
        intent_data: dict,
        experience_data: dict,
        budget_data: dict,
    ) -> str:
        experience_plan = experience_data.get("experience_plan", [])
        if experience_plan:
            return str(experience_plan[0].get("destination", ""))

        if intent_data.get("destination_preference"):
            return str(intent_data["destination_preference"])

        budget_items = budget_data.get("budget_analysis", [])
        if budget_items:
            destination_label = str(budget_items[0].get("destination", ""))
            return destination_label.split(",")[0].strip()

        return "the destination"

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
        for option in itinerary.get("trip_options", []):
            text_parts.append(option.get("summary", ""))
            text_parts.append(option.get("tradeoff", ""))
        for day in itinerary.get("itinerary", []):
            text_parts.append(day.get("theme", ""))
            text_parts.append(day.get("local_transport_strategy", ""))
            for item in day.get("plan", []):
                text_parts.append(item.get("place", ""))
                text_parts.append(item.get("activity", ""))
                text_parts.append(item.get("reason_to_visit", ""))
                text_parts.append(item.get("notes", ""))
                text_parts.append(item.get("backup_option", ""))

        combined = " ".join(text_parts).lower()
        return any(term in combined for term in generic_terms)
