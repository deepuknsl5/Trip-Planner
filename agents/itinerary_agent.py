# agents/itinerary_agent.py
from datetime import datetime, timedelta
from typing import Dict

from llm.openai_client import call_openai
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
- If trip duration ≤ 7 days → ONLY ONE destination
- Do NOT include inter-country or long-haul travel inside itinerary
- Prioritize relaxation and human pacing
- Maximum 3–4 activities per day
- Include buffer time, rest, and flexibility
- Respect local meal times and attraction hours
- Use 24-hour time format (HH:MM)
- Output MUST be valid JSON ONLY
"""

    def _generate_dates(self, days: int) -> Dict[str, str]:
        start = datetime.now().date() + timedelta(days=1)
        return {
            f"Day {i+1}": (start + timedelta(days=i)).isoformat()
            for i in range(days)
        }

    def execute(self, intent_data: dict, experience_data: dict) -> dict:
        duration = int(intent_data.get("duration_days", 5))
        companions = intent_data.get("companions", "travelers")

        # 🔒 Enforce realism: ONE destination only
        primary_destination = experience_data["experience_plan"][0]["destination"]

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

TASK:
Create a {duration}-day itinerary for {companions}.
Ensure relaxed pacing, realistic timing, and logical flow.
"""

        itinerary = convert_to_model(
            input_text=user_prompt,
            target_model=ItineraryResult
        )

        return itinerary.model_dump()
