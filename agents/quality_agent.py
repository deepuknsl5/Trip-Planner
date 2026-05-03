from typing import Any, Dict

from llm.structured_output import convert_to_model
from models.quality import PlanQualityReport
from models.travel_plan import EditableTravelPlan


class QualityAgent:
    """
    Validates that the final plan feels usable, practical, and personalized.
    """

    def __init__(self):
        self.name = "Quality Reviewer"

    def assess(self, user_input: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are reviewing a travel plan before it is shown to the user.

USER REQUEST:
{user_input}

CURRENT PLAN:
{plan}

THE USER SHOULD AGREE WITH ALL THREE:
- "This saved me time"
- "This plan actually works"
- "It feels personalized"

QUALITY BAR:
- saves_time = true only if the plan is decision-ready and reduces research effort
- works_in_real_world = true only if the plan has realistic pacing, timings, movement, and cost logic
- feels_personalized = true only if the plan clearly reflects the user's destination, budget, companions, and stated preferences
- revision_required = true if any of the three checks should be false
- revision_instructions must be concrete and operational, not vague
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=PlanQualityReport,
        )
        return result.model_dump()

    def revise(
        self,
        user_input: str,
        plan: Dict[str, Any],
        quality_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
You are improving a travel plan after quality review.

USER REQUEST:
{user_input}

CURRENT PLAN:
{plan}

QUALITY REVIEW:
{quality_report}

TASK:
Return the FULL improved travel plan JSON.

MANDATORY RULES:
- Fix the specific issues in revision_instructions.
- The final plan must make the user agree with all three:
  - "This saved me time"
  - "This plan actually works"
  - "It feels personalized"
- Preserve correct details already present.
- Do not make the plan more generic.
- Keep the itinerary practical, with realistic timings, transit, buffers, and costs.
- Keep the plan aligned with the user's budget level, companions, and destination.
- Keep Plan A and Plan B.
- Tighten explanations so the user can act on them quickly.
- Return valid JSON matching the schema only.
"""
        result = convert_to_model(
            input_text=prompt,
            target_model=EditableTravelPlan,
        )
        return result.model_dump()
