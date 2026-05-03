from typing import Any, Dict

from llm.structured_output import convert_to_model
from models.plan_edit import PlanEditIntent
from models.travel_plan import EditableTravelPlan


class PlanEditAgent:
    """
    Detects edit-style follow-ups and updates the existing trip plan.
    """

    def __init__(self):
        self.name = "Plan Editor"

    def detect(self, user_input: str, previous_result: Dict[str, Any]) -> Dict[str, Any]:
        plan_snapshot = previous_result.get("editable_plan") or previous_result.get("travel_plan", {})
        prompt = f"""
You are deciding whether a follow-up user message is an edit to an existing travel plan.

EXISTING PLAN SNAPSHOT:
{plan_snapshot}

USER MESSAGE:
{user_input}

RULES:
- Set is_plan_edit = true when the user is clearly changing the current plan.
- Examples of edits: make it cheaper, add nightlife, remove museums, swap activities, reduce travel, add food stops, shorten a day, make it family friendly.
- Set is_plan_edit = false if the user is starting a new trip, asking for a different destination, or making a fresh planning request unrelated to the current plan.
- response_focus should usually be:
  - budget for cost-cutting edits
  - experiences for add/remove activity category edits
  - itinerary for schedule or pacing edits
  - full_trip when multiple sections will change
- keep_destination should stay true unless the user explicitly wants a different destination.
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=PlanEditIntent,
        )
        return result.model_dump()

    def execute(
        self,
        user_input: str,
        previous_plan: Dict[str, Any],
        edit_intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
You are editing an EXISTING travel plan.

CURRENT PLAN:
{previous_plan}

EDIT INTENT:
{edit_intent}

USER EDIT REQUEST:
{user_input}

TASK:
Return the FULL updated travel plan JSON.

MANDATORY RULES:
- Edit the existing plan instead of regenerating blindly from scratch.
- Preserve the current destination, duration, companions, and valid unchanged sections unless the user explicitly requests otherwise.
- Keep as much of the existing structure as possible.
- Only change the sections required by the edit request.
- If the request is about cost:
  - reduce expensive activities, transport, or stay assumptions where realistic
  - update budget_analysis, itinerary stop costs, day costs, and trip options consistently
- If the request adds an activity style like nightlife:
  - update experiences and itinerary with realistic timings and nearby placement
- If the request removes an activity type like museums:
  - remove those stops from experiences and itinerary
  - replace them with realistic alternatives or rest instead of leaving holes
- Keep itinerary timings realistic, including transit times and buffers.
- Keep Plan A and Plan B, but adjust them to reflect the edit.
- Keep assumptions concise and update them only if the edit changes them.
- Update planner_brief so it reflects the edited plan.
- Return valid JSON matching the schema only.
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=EditableTravelPlan,
        )
        result_dict = result.model_dump()
        budget_items = result_dict.get("budget_analysis", {}).get("budget_analysis", [])
        result_dict["feasible_destinations"] = [
            item
            for item in budget_items
            if item.get("feasibility") in ("feasible", "tight_but_feasible")
        ]
        return result_dict
