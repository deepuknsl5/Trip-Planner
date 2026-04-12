from typing import Any, Dict

from agents.budget_agent import BudgetAgent
from agents.destination_agent import DestinationAgent
from agents.experience_agent import ExperienceAgent
from agents.intent_agent import IntentAgent
from agents.itinerary_agent import ItineraryAgent


class TravelPlannerCoordinator:
    """
    Central orchestration layer that controls execution order,
    enforces feasibility rules, and maintains consistency
    across all planning agents.
    """

    def __init__(self):
        self.intent_agent = IntentAgent()
        self.destination_agent = DestinationAgent()
        self.budget_agent = BudgetAgent()
        self.experience_agent = ExperienceAgent()
        self.itinerary_agent = ItineraryAgent()

    def run(self, user_input: str) -> Dict[str, Any]:
        pipeline_log = []
        context: Dict[str, Any] = {}

        intent = self.intent_agent.execute(user_input)
        pipeline_log.append(f"IntentAgent: Extracted intent -> {intent}")

        if not intent or "error" in intent:
            return self._fail("IntentAgent", intent, pipeline_log)

        if not intent.get("is_travel_request", True):
            return {
                "status": "unsupported_request",
                "message": "This system only handles trip planning requests.",
                "supported_examples": [
                    "Plan a 3-day trip to Jaipur on a moderate budget",
                    "Give me an itinerary for Vaishno Devi",
                    "Suggest hill stations near Delhi for a weekend trip",
                    "Estimate the budget for a Goa trip for 2 people",
                ],
                "intent": intent,
                "pipeline_log": pipeline_log,
            }

        context["intent"] = intent
        context["assumptions"] = self._build_assumptions(intent, user_input)

        if intent.get("destination_preference"):
            destinations = {
                "recommended_destinations": [
                    {
                        "name": intent["destination_preference"],
                        "country": intent.get("country_preference", "Unknown"),
                        "why_suitable": "User-specified destination",
                        "best_for": [],
                        "budget_range": intent.get("budget_level", "unknown"),
                        "ideal_duration": f"{intent.get('duration_days', 3)} days",
                        "best_season": "All year",
                        "pros": ["Matches user intent"],
                        "cons": [],
                    }
                ]
            }
            pipeline_log.append(
                f"DestinationAgent skipped -> using user destination: {intent['destination_preference']}"
            )
        else:
            destinations = self.destination_agent.execute(intent)
            pipeline_log.append(f"DestinationAgent -> {destinations}")
            if not destinations or not destinations.get("recommended_destinations"):
                return self._fail("DestinationAgent", destinations, pipeline_log)

        context["destinations"] = destinations

        budget_analysis = self.budget_agent.execute(intent, destinations)
        pipeline_log.append(f"BudgetAgent -> {budget_analysis}")

        feasible_destinations = self.budget_agent.get_feasible_destinations(budget_analysis)
        if not feasible_destinations:
            return {
                "status": "no_feasible_plan",
                "message": "All destinations exceed budget constraints",
                "intent": intent,
                "destinations": destinations,
                "budget_analysis": budget_analysis,
                "pipeline_log": pipeline_log,
            }

        context["budget_analysis"] = budget_analysis
        context["feasible_destinations"] = feasible_destinations

        experiences = self.experience_agent.execute(
            intent_data=intent,
            budget_data=budget_analysis,
        )
        pipeline_log.append(f"ExperienceAgent -> {experiences}")

        if not experiences or not experiences.get("experience_plan"):
            experiences = {
                "warning": "No curated experiences generated",
                "experience_plan": [],
            }

        context["experiences"] = experiences

        itinerary = self.itinerary_agent.execute(
            intent_data=intent,
            experience_data=experiences,
        )
        pipeline_log.append(f"ItineraryAgent -> {itinerary}")

        if not itinerary or (isinstance(itinerary, dict) and "error" in itinerary):
            itinerary = {
                "warning": "Itinerary generation incomplete",
                "details": itinerary,
            }

        context["itinerary"] = itinerary

        response_focus = intent.get("response_focus", "full_trip")
        planner_brief = self._build_planner_brief(response_focus, context)
        context["planner_brief"] = planner_brief

        compact_travel_plan = self._build_compact_travel_plan(response_focus, context)

        return {
            "status": "success",
            "response_focus": response_focus,
            "primary_result": self._build_primary_result(response_focus, compact_travel_plan),
            "planner_brief": planner_brief,
            "assumptions": context.get("assumptions", []),
            "travel_plan": compact_travel_plan,
            "pipeline_log": pipeline_log,
        }

    def _fail(
        self,
        stage: str,
        details: Any,
        pipeline_log: list,
    ) -> Dict[str, Any]:
        return {
            "status": "failed",
            "failed_stage": stage,
            "details": details,
            "pipeline_log": pipeline_log,
        }

    def _build_primary_result(
        self,
        response_focus: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        mapping = {
            "itinerary": ("itinerary", "Requested Itinerary"),
            "budget": ("budget_analysis", "Requested Budget View"),
            "destination": ("destinations", "Requested Destination View"),
            "experiences": ("experiences", "Requested Experiences View"),
            "full_trip": ("itinerary", "Trip Plan Overview"),
        }

        section_key, title = mapping.get(
            response_focus,
            ("itinerary", "Trip Plan Overview"),
        )

        return {
            "focus": response_focus,
            "title": title,
            "data": context.get(section_key, {}),
        }

    def _build_compact_travel_plan(
        self,
        response_focus: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        base = {
            "intent": context.get("intent", {}),
            "assumptions": context.get("assumptions", []),
            "destinations": context.get("destinations", {}),
            "planner_brief": context.get("planner_brief"),
        }

        if response_focus == "itinerary":
            base["itinerary"] = context.get("itinerary", {})
            return base

        if response_focus == "budget":
            base["budget_analysis"] = context.get("budget_analysis", {})
            base["feasible_destinations"] = context.get("feasible_destinations", [])
            return base

        if response_focus == "destination":
            return base

        if response_focus == "experiences":
            base["experiences"] = context.get("experiences", {})
            return base

        return context

    def _build_assumptions(
        self,
        intent: Dict[str, Any],
        user_input: str,
    ) -> list[str]:
        assumptions = []
        normalized = user_input.lower()

        if "day" not in normalized and "night" not in normalized and "weekend" not in normalized:
            assumptions.append(
                f"Duration was assumed as {intent.get('duration_days', 3)} day(s) because it was not specified."
            )

        if intent.get("companions", "solo") == "solo" and not any(
            token in normalized for token in ["with ", "couple", "family", "friends", "group", "partner"]
        ):
            assumptions.append("Companions were assumed as solo because no travel group was mentioned.")

        if intent.get("budget_level") == "unknown":
            assumptions.append(
                "Budget was not specified, so practical mid-range options were used where needed."
            )

        if not intent.get("origin"):
            assumptions.append(
                "Origin was not provided, so getting to the destination was not optimized."
            )

        if not any(
            token in normalized
            for token in [
                "today", "tomorrow", "next weekend", "this weekend", "january", "february", "march",
                "april", "may", "june", "july", "august", "september", "october", "november", "december",
            ]
        ):
            assumptions.append(
                "Exact travel dates were not provided, so the plan focuses on trip structure rather than date-specific timings."
            )

        return assumptions

    def _build_planner_brief(
        self,
        response_focus: str,
        context: Dict[str, Any],
    ) -> str:
        intent = context.get("intent", {})
        destinations = context.get("destinations", {}).get("recommended_destinations", [])
        destination_name = destinations[0]["name"] if destinations else "your destination"
        duration = intent.get("duration_days", "N/A")

        if response_focus == "itinerary":
            return f"{duration}-day itinerary prepared for {destination_name} with practical pacing and the most relevant stops first."
        if response_focus == "budget":
            return f"Budget view prepared for {destination_name} with a practical estimate and clear assumptions."
        if response_focus == "destination":
            return "Destination recommendations prepared based on the trip constraints detected from the prompt."
        if response_focus == "experiences":
            return f"Experience shortlist prepared for {destination_name} with activities that fit the trip intent."
        return f"{duration}-day trip plan prepared for {destination_name} with itinerary, budget, and supporting details."
