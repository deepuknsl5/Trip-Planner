from llm.structured_output import convert_to_model
from models.intent import TravelIntent


class IntentAgent:
    """
    IntentAgent converts free-form user input
    into structured TravelIntent data.
    """

    def __init__(self):
        self.name = "Intent Analyzer"
        self.role = "Extract structured travel intent from user input"

    def execute(self, user_input: str) -> dict:
        """
        Convert raw user text into a validated TravelIntent model.
        """

        prompt = f"""
Extract structured travel intent from user input.

IMPORTANT EXTRACTION RULES:
- This system is a TRIP PLANNER, not a general chatbot.
- If the request is not about trip planning, itinerary creation, destination discovery, travel budgeting, or travel activities:
  - set is_travel_request = false
  - keep other fields at safe defaults
- Set `origin` ONLY if the user explicitly states where they are starting from.
- Do NOT infer `origin` from the destination.
- If the user says "from Delhi", then origin = Delhi.
- If the user asks for an outing or activities "in Delhi" without travel language, treat it as a local plan:
  - trip_scope = "local_outing"
  - destination_preference = Delhi
  - origin = null unless explicitly stated
- If the request is a normal travel plan, set trip_scope = "trip".
- Detect the primary response focus:
  - itinerary, schedule, day-wise plan -> response_focus = "itinerary"
  - budget, cost, cheap, affordable -> response_focus = "budget"
  - destination suggestions or comparison -> response_focus = "destination"
  - activities or things to do -> response_focus = "experiences"
  - otherwise -> response_focus = "full_trip"
- Identify destination if explicitly mentioned.
- Identify country if implied.
- If user says "Himachal", map country_preference to India.
- If no budget is mentioned, budget_level = "unknown".
- If companions are not mentioned, use companions = "solo".
- If user says "next weekend" or "this weekend", use duration_days = 2.
- If duration is not mentioned:
  - for local_outing use duration_days = 2
  - otherwise use duration_days = 3
- Normalize obvious place spellings when safe:
  - "Vaishnodevi" -> "Vaishno Devi"
- Keep special_preferences concise and only include explicit user preferences.

USER INPUT:
{user_input}
        """

        intent: TravelIntent = convert_to_model(
            input_text=prompt,
            target_model=TravelIntent
        )

        intent_dict = intent.model_dump()
        intent_dict["destination_preference"] = self._normalize_destination(
            intent_dict.get("destination_preference")
        )
        intent_dict["response_focus"] = self._infer_response_focus(
            user_input,
            intent_dict.get("response_focus", "full_trip"),
        )
        return intent_dict

    def _normalize_destination(self, destination: str | None) -> str | None:
        if not destination:
            return destination

        normalized = destination.strip().lower()
        known_names = {
            "vaishnodevi": "Vaishno Devi",
            "vaishno devi": "Vaishno Devi",
        }
        return known_names.get(normalized, destination)

    def _infer_response_focus(self, user_input: str, extracted_focus: str) -> str:
        normalized = " ".join(user_input.lower().split())

        if any(token in normalized for token in ["budget", "cost", "cheap", "affordable", "price"]):
            return "budget"

        if any(token in normalized for token in ["suggest", "recommend", "where should", "best places", "compare"]):
            return "destination"

        if any(token in normalized for token in ["things to do", "activities", "what to do", "experiences"]):
            return "experiences"

        if any(token in normalized for token in ["itinerary", "schedule", "day-wise", "day wise", "day by day"]):
            return "itinerary"

        if any(
            phrase in normalized
            for phrase in [
                "plan my trip to",
                "plan a trip to",
                "plan trip to",
                "plan my travel to",
                "trip to ",
            ]
        ):
            return "itinerary"

        return extracted_focus or "full_trip"
