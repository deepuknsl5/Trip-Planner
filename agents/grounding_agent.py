from typing import Any, Dict

from llm.structured_output import convert_to_model
from models.grounding import GroundingReport
from models.travel_plan import EditableTravelPlan


class GroundingAgent:
    """
    Reviews plan outputs for unsupported specificity and cross-agent contradictions.
    """

    def __init__(self):
        self.name = "Grounding Reviewer"

    def assess(self, user_input: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are reviewing a travel plan for hallucination risk.

IMPORTANT CONTEXT:
- This plan was produced by multiple planning agents.
- Do NOT assume external live maps, opening-hours data, ratings, or verified venue databases were used.
- If a detail cannot be strongly justified from common high-level travel knowledge or the user request, it should be downgraded to a safer estimate or area-level wording.

USER REQUEST:
{user_input}

CURRENT PLAN:
{plan}

CHECK FOR THESE RISKS:
- invented exact venue, restaurant, hotel, or business names
- made-up opening hours, ratings, crowd predictions, or queue claims
- fake precision in travel time or pricing stated as certainty instead of estimate
- cross-section contradictions between destination, budget, experiences, and itinerary
- itinerary stops that look too specific for an unsourced planner

REVIEW RULES:
- safe_to_return should be false if the plan sounds overly certain without grounding
- avoids_invented_specifics should be false if the plan uses unsupported exact details
- uses_estimates_not_fake_precision should be false if costs or timings are presented as guaranteed facts
- revision_required should be true if any risk is material
- revision_instructions must tell the editor exactly how to make the plan safer
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=GroundingReport,
        )
        return result.model_dump()

    def revise(
        self,
        user_input: str,
        plan: Dict[str, Any],
        grounding_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
You are revising a travel plan to remove hallucination risk.

IMPORTANT CONTEXT:
- This plan must not pretend to know live tool data or verified venue facts.
- If exact places are uncertain, prefer famous landmark names, neighborhood names, or area-level stops.
- Costs and local travel times must remain estimates, not guaranteed facts.

USER REQUEST:
{user_input}

CURRENT PLAN:
{plan}

GROUNDING REVIEW:
{grounding_report}

TASK:
Return the FULL safer travel plan JSON.

MANDATORY RULES:
- Remove or generalize unsupported specifics.
- Do not invent exact business names, ratings, opening hours, or live availability claims.
- Replace risky precision with practical estimates and clear notes.
- Keep the plan useful and personalized while making it safer.
- Keep sections internally consistent.
- Keep Plan A and Plan B.
- Return valid JSON matching the schema only.
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=EditableTravelPlan,
        )
        return result.model_dump()
