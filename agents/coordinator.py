# # agents/coordinator.py

# from agents.intent_agent import IntentAgent
# from agents.destination_agent import DestinationAgent
# from agents.budget_agent import BudgetAgent
# from agents.experience_agent import ExperienceAgent
# from agents.itinerary_agent import ItineraryAgent


# class TravelPlannerCoordinator:
#     """
#     TravelPlannerCoordinator orchestrates all agents
#     to generate a complete travel plan.
#     """

#     def __init__(self):
#         self.intent_agent = IntentAgent()
#         self.destination_agent = DestinationAgent()
#         self.budget_agent = BudgetAgent()
#         self.experience_agent = ExperienceAgent()
#         self.itinerary_agent = ItineraryAgent()

#     def run(self, user_input: str) -> dict:
#         """
#         Executes the full multi-agent pipeline.
#         """

#         result = {}

#         # 1. Understand intent
#         intent = self.intent_agent.execute(user_input)
#         result["intent"] = intent

#         if "error" in intent:
#             return {
#                 "error": "Failed at intent analysis",
#                 "details": intent
#             }

#         # 2. Suggest destinations
#         destinations = self.destination_agent.execute(intent)
#         result["destinations"] = destinations

#         # 3. Analyze budget feasibility
#         budget_analysis = self.budget_agent.execute(intent, destinations)
#         result["budget_analysis"] = budget_analysis

#         # 4. Curate experiences
#         experiences = self.experience_agent.execute(intent, budget_analysis)
#         result["experiences"] = experiences

#         # 5. Build itinerary
#         itinerary = self.itinerary_agent.execute(intent, experiences)
#         result["itinerary"] = itinerary

#         return result


from typing import Dict, Any

from agents.intent_agent import IntentAgent
from agents.destination_agent import DestinationAgent
from agents.budget_agent import BudgetAgent
from agents.experience_agent import ExperienceAgent
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
        """
        Executes the complete travel planning pipeline.
        """

        pipeline_log = []
        context: Dict[str, Any] = {}

        # -------------------------------------------------
        # 1. INTENT (SOURCE OF TRUTH)
        # -------------------------------------------------
        intent = self.intent_agent.execute(user_input)
        pipeline_log.append("IntentAgent → structured travel intent")

        if not intent or "error" in intent:
            return self._fail("IntentAgent", intent, pipeline_log)

        context["intent"] = intent

        # -------------------------------------------------
        # 2. DESTINATION DISCOVERY
        # -------------------------------------------------
        destinations = self.destination_agent.execute(intent)
        pipeline_log.append("DestinationAgent → destination recommendations")

        if not destinations or not destinations.get("recommended_destinations"):
            return self._fail("DestinationAgent", destinations, pipeline_log)

        context["destinations"] = destinations

        # -------------------------------------------------
        # 3. BUDGET FEASIBILITY (HARD GATE)
        # -------------------------------------------------
        budget_analysis = self.budget_agent.execute(intent, destinations)
        pipeline_log.append("BudgetAgent → budget feasibility analysis")

        feasible_destinations = self.budget_agent.get_feasible_destinations(
            budget_analysis
        )

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

        # -------------------------------------------------
        # 4. EXPERIENCE CURATION (FEASIBLE ONLY)
        # -------------------------------------------------
        experiences = self.experience_agent.execute(
            intent_data=intent,
            budget_data=budget_analysis,
        )
        pipeline_log.append("ExperienceAgent → curated experiences")

        if not experiences or not experiences.get("experience_plan"):
            experiences = {
                "warning": "No curated experiences generated",
                "experience_plan": [],
            }

        context["experiences"] = experiences

        # -------------------------------------------------
        # 5. ITINERARY CONSTRUCTION
        # -------------------------------------------------
        itinerary = self.itinerary_agent.execute(
            intent_data=intent,
            experience_data=experiences,
        )
        pipeline_log.append("ItineraryAgent → final itinerary")

        if not itinerary or isinstance(itinerary, dict) and "error" in itinerary:
            itinerary = {
                "warning": "Itinerary generation incomplete",
                "details": itinerary,
            }

        context["itinerary"] = itinerary

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------
        return {
            "status": "success",
            "travel_plan": context,
            "pipeline_log": pipeline_log,
        }

    # -------------------------------------------------
    # INTERNAL ERROR HANDLING
    # -------------------------------------------------

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
