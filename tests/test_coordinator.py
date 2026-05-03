import unittest
from unittest.mock import Mock

from agents.coordinator import TravelPlannerCoordinator


def sample_intent(**overrides):
    base = {
        "is_travel_request": True,
        "travel_purpose": "trip",
        "travel_type": "plan",
        "budget_level": "moderate",
        "trip_scope": "trip",
        "response_focus": "full_trip",
        "duration_days": 3,
        "companions": "solo",
        "origin": "Delhi",
        "destination_preference": "Jaipur",
        "country_preference": "India",
        "special_preferences": [],
    }
    base.update(overrides)
    return base


def sample_destinations():
    return {
        "recommended_destinations": [
            {
                "name": "Jaipur",
                "country": "India",
                "why_suitable": "Good match",
                "best_for": ["culture"],
                "budget_range": "moderate",
                "ideal_duration": "3 days",
                "best_season": "Winter",
                "pros": ["Compact"],
                "cons": ["Crowded"],
            }
        ]
    }


def sample_budget(feasibility="feasible"):
    return {
        "budget_analysis": [
            {
                "destination": "Jaipur, India",
                "feasibility": feasibility,
                "estimated_total_cost": "INR 18,000",
                "cost_breakdown": {
                    "transport": "INR 4,000",
                    "stay": "INR 7,000",
                    "food": "INR 3,000",
                    "activities": "INR 4,000",
                },
                "reason": "Fits the budget.",
                "pricing_notes": ["Shoulder-season pricing"],
                "suggested_adjustments": [],
            }
        ]
    }


def sample_experiences():
    return {
        "experience_plan": [
            {
                "destination": "Jaipur",
                "signature_experiences": [
                    {
                        "title": "Amber Fort",
                        "category": "culture",
                        "description": "Fort visit",
                        "why_special": "Historic",
                        "duration": "3 hours",
                        "best_time": "Morning",
                        "budget_category": "moderate",
                        "approximate_cost": "INR 800",
                        "insider_tips": ["Arrive early"],
                    }
                ],
                "additional_experiences": [],
                "free_activities": [],
            }
        ]
    }


def sample_itinerary():
    return {
        "trip_style": "balanced",
        "planning_logic": "Grouped nearby stops.",
        "internal_transport_tip": "Use cabs for fort clusters.",
        "trip_options": [
            {
                "label": "Plan A",
                "summary": "Balanced route",
                "best_for": "First-time visitors",
                "tradeoff": "Moderate spend",
                "estimated_total_cost": "INR 18,000",
            },
            {
                "label": "Plan B",
                "summary": "Cheaper route",
                "best_for": "Budget travelers",
                "tradeoff": "Fewer paid stops",
                "estimated_total_cost": "INR 14,000",
            },
        ],
        "itinerary": [
            {
                "day": "Day 1",
                "date": "2026-04-28",
                "zone": "Old Jaipur",
                "theme": "Arrival and core sights",
                "start_time": "08:00",
                "end_time": "20:30",
                "estimated_day_cost": "INR 6,000",
                "local_transport_strategy": "Cluster nearby sights.",
                "plan": [
                    {
                        "start_time": "08:00",
                        "end_time": "10:00",
                        "place": "Amber Fort",
                        "activity": "Explore the fort",
                        "category": "culture",
                        "transit_mode_from_previous": None,
                        "transit_time_from_previous_minutes": None,
                        "buffer_minutes": 15,
                        "estimated_cost": "INR 800",
                        "reason_to_visit": "Iconic landmark",
                        "notes": "Buy tickets in advance",
                        "backup_option": "City Palace",
                    }
                ],
            }
        ],
    }


def sample_editable_plan():
    budget = sample_budget()
    return {
        "intent": sample_intent(),
        "assumptions": ["Existing assumptions"],
        "destinations": sample_destinations(),
        "budget_analysis": budget,
        "feasible_destinations": budget["budget_analysis"],
        "experiences": sample_experiences(),
        "itinerary": sample_itinerary(),
        "planner_brief": "Existing planner brief.",
    }


class TravelPlannerCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = TravelPlannerCoordinator()

    def configure_fresh_pipeline(self, intent=None, budget=None, experiences=None, itinerary=None):
        intent = intent or sample_intent()
        budget = budget or sample_budget()
        experiences = experiences if experiences is not None else sample_experiences()
        itinerary = itinerary if itinerary is not None else sample_itinerary()

        self.coordinator.intent_agent.execute = Mock(return_value=intent)
        self.coordinator.destination_agent.execute = Mock(return_value=sample_destinations())
        self.coordinator.budget_agent.execute = Mock(return_value=budget)
        self.coordinator.budget_agent.get_feasible_destinations = Mock(
            return_value=[
                item
                for item in budget.get("budget_analysis", [])
                if item.get("feasibility") in ("feasible", "tight_but_feasible")
            ]
        )
        self.coordinator.experience_agent.execute = Mock(return_value=experiences)
        self.coordinator.itinerary_agent.execute = Mock(return_value=itinerary)
        self.coordinator.grounding_agent.assess = Mock(
            return_value={
                "safe_to_return": True,
                "avoids_invented_specifics": True,
                "consistent_across_sections": True,
                "uses_estimates_not_fake_precision": True,
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.grounding_agent.revise = Mock()
        self.coordinator.quality_agent.assess = Mock(
            return_value={
                "saves_time": True,
                "works_in_real_world": True,
                "feels_personalized": True,
                "strengths": ["Actionable route"],
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.quality_agent.revise = Mock()

    def test_fresh_plan_success_builds_editable_plan(self):
        self.configure_fresh_pipeline()

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.assertIn("editable_plan", result)
        self.assertIn("itinerary", result["editable_plan"])
        self.assertTrue(result["grounding_report"]["safe_to_return"])
        self.assertTrue(result["quality_report"]["saves_time"])
        self.coordinator.destination_agent.execute.assert_not_called()
        self.coordinator.itinerary_agent.execute.assert_called_once()

    def test_iterative_edit_uses_existing_plan_without_fresh_regeneration(self):
        previous_result = {
            "response_focus": "full_trip",
            "editable_plan": sample_editable_plan(),
        }
        updated_context = sample_editable_plan()
        updated_context["planner_brief"] = "Budget-friendly edit applied."

        self.coordinator.plan_edit_agent.detect = Mock(
            return_value={
                "is_plan_edit": True,
                "summary": "Make the current Jaipur plan cheaper.",
                "response_focus": "budget",
                "keep_destination": True,
                "requested_changes": ["Reduce total cost"],
            }
        )
        self.coordinator.plan_edit_agent.execute = Mock(return_value=updated_context)
        self.coordinator.grounding_agent.assess = Mock(
            return_value={
                "safe_to_return": True,
                "avoids_invented_specifics": True,
                "consistent_across_sections": True,
                "uses_estimates_not_fake_precision": True,
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.grounding_agent.revise = Mock()
        self.coordinator.quality_agent.assess = Mock(
            return_value={
                "saves_time": True,
                "works_in_real_world": True,
                "feels_personalized": True,
                "strengths": ["Edit preserved route quality"],
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.quality_agent.revise = Mock()
        self.coordinator.intent_agent.execute = Mock(side_effect=AssertionError("fresh pipeline should not run"))

        result = self.coordinator.run(
            user_input="PREVIOUS CONTEXT:\n- old\nCURRENT REQUEST:\nmake it cheaper",
            previous_result=previous_result,
            raw_user_input="make it cheaper",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "iterative_edit")
        self.assertEqual(result["response_focus"], "budget")
        self.assertEqual(result["edit_summary"], "Make the current Jaipur plan cheaper.")
        self.assertIn("budget_analysis", result["travel_plan"])
        self.assertIn("feasible_destinations", result["travel_plan"])
        self.assertTrue(result["grounding_report"]["avoids_invented_specifics"])
        self.assertTrue(result["quality_report"]["works_in_real_world"])
        self.coordinator.plan_edit_agent.detect.assert_called_once_with("make it cheaper", previous_result)
        self.coordinator.plan_edit_agent.execute.assert_called_once()

    def test_edit_request_falls_back_to_fresh_generation_when_previous_result_is_not_editable(self):
        previous_result = {
            "travel_plan": {
                "intent": {"destination_preference": "Jaipur"},
            }
        }

        self.coordinator.plan_edit_agent.detect = Mock(
            return_value={
                "is_plan_edit": True,
                "summary": "Remove museums",
                "response_focus": "experiences",
                "keep_destination": True,
                "requested_changes": ["Remove museums"],
            }
        )
        self.coordinator.plan_edit_agent.execute = Mock()
        self.configure_fresh_pipeline()

        result = self.coordinator.run(
            user_input="PREVIOUS CONTEXT:\n- old\nCURRENT REQUEST:\nremove museums",
            previous_result=previous_result,
            raw_user_input="remove museums",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.assertTrue(
            any("fallback" in step.lower() for step in result["pipeline_log"])
        )
        self.coordinator.plan_edit_agent.execute.assert_not_called()
        self.coordinator.intent_agent.execute.assert_called_once()

    def test_non_edit_follow_up_continues_with_fresh_generation(self):
        previous_result = {
            "response_focus": "full_trip",
            "editable_plan": sample_editable_plan(),
        }
        self.coordinator.plan_edit_agent.detect = Mock(
            return_value={
                "is_plan_edit": False,
                "summary": "New trip request",
                "response_focus": "full_trip",
                "keep_destination": False,
                "requested_changes": [],
            }
        )
        self.coordinator.plan_edit_agent.execute = Mock()
        self.configure_fresh_pipeline()

        result = self.coordinator.run(
            user_input="plan a trip to Goa",
            previous_result=previous_result,
            raw_user_input="plan a trip to Goa",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.coordinator.plan_edit_agent.execute.assert_not_called()
        self.coordinator.intent_agent.execute.assert_called_once()

    def test_unsupported_request_short_circuits_pipeline(self):
        self.coordinator.intent_agent.execute = Mock(
            return_value={
                "is_travel_request": False,
                "response_focus": "full_trip",
            }
        )
        self.coordinator.destination_agent.execute = Mock(side_effect=AssertionError("should not run"))

        result = self.coordinator.run("write me a poem")

        self.assertEqual(result["status"], "unsupported_request")
        self.assertIn("supported_examples", result)

    def test_no_feasible_plan_stops_before_experience_generation(self):
        intent = sample_intent(destination_preference=None)
        budget = sample_budget(feasibility="not_feasible")
        self.configure_fresh_pipeline(intent=intent, budget=budget)
        self.coordinator.budget_agent.get_feasible_destinations = Mock(return_value=[])
        self.coordinator.experience_agent.execute = Mock(side_effect=AssertionError("should not run"))

        result = self.coordinator.run("plan a Jaipur trip")

        self.assertEqual(result["status"], "no_feasible_plan")
        self.assertEqual(result["budget_analysis"], budget)

    def test_missing_experiences_and_bad_itinerary_degrade_gracefully(self):
        intent = sample_intent()
        self.configure_fresh_pipeline(intent=intent, experiences={}, itinerary={"error": "bad output"})

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.assertEqual(result["travel_plan"]["experiences"]["warning"], "No curated experiences generated")
        self.assertEqual(result["travel_plan"]["itinerary"]["warning"], "Itinerary generation incomplete")

    def test_iterative_edit_can_use_full_travel_plan_when_editable_plan_is_missing(self):
        full_travel_plan = sample_editable_plan()
        previous_result = {
            "response_focus": "full_trip",
            "travel_plan": full_travel_plan,
        }
        self.coordinator.plan_edit_agent.detect = Mock(
            return_value={
                "is_plan_edit": True,
                "summary": "Add nightlife",
                "response_focus": "itinerary",
                "keep_destination": True,
                "requested_changes": ["Add nightlife"],
            }
        )
        self.coordinator.plan_edit_agent.execute = Mock(return_value=full_travel_plan)
        self.coordinator.grounding_agent.assess = Mock(
            return_value={
                "safe_to_return": True,
                "avoids_invented_specifics": True,
                "consistent_across_sections": True,
                "uses_estimates_not_fake_precision": True,
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.grounding_agent.revise = Mock()
        self.coordinator.quality_agent.assess = Mock(
            return_value={
                "saves_time": True,
                "works_in_real_world": True,
                "feels_personalized": True,
                "strengths": ["Edit remained personalized"],
                "issues": [],
                "revision_required": False,
                "revision_instructions": [],
            }
        )
        self.coordinator.quality_agent.revise = Mock()
        self.coordinator.intent_agent.execute = Mock(side_effect=AssertionError("fresh pipeline should not run"))

        result = self.coordinator.run(
            user_input="add nightlife",
            previous_result=previous_result,
            raw_user_input="add nightlife",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "iterative_edit")
        self.assertIn("itinerary", result["travel_plan"])

    def test_grounding_gate_revises_unsafe_plan_before_quality_pass(self):
        self.configure_fresh_pipeline()
        revised_context = sample_editable_plan()
        revised_context["planner_brief"] = "Generalized unsupported specifics and kept practical estimates."
        self.coordinator.grounding_agent.assess = Mock(
            return_value={
                "safe_to_return": False,
                "avoids_invented_specifics": False,
                "consistent_across_sections": True,
                "uses_estimates_not_fake_precision": False,
                "issues": ["Place names are too specific", "Travel times look overly certain"],
                "revision_required": True,
                "revision_instructions": ["Generalize risky stops", "Convert hard claims to estimates"],
            }
        )
        self.coordinator.grounding_agent.revise = Mock(return_value=revised_context)

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["planner_brief"],
            "Generalized unsupported specifics and kept practical estimates.",
        )
        self.coordinator.grounding_agent.revise.assert_called_once()

    def test_grounding_gate_failure_does_not_break_plan_generation(self):
        self.configure_fresh_pipeline()
        self.coordinator.grounding_agent.assess = Mock(side_effect=RuntimeError("grounding service failed"))

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.assertEqual(result.get("grounding_report", {}), {})
        self.assertTrue(any("GroundingAgent skipped" in step for step in result["pipeline_log"]))

    def test_quality_gate_revises_weak_fresh_plan(self):
        self.configure_fresh_pipeline()
        revised_context = sample_editable_plan()
        revised_context["planner_brief"] = "Revised to be faster, more practical, and more personal."
        self.coordinator.quality_agent.assess = Mock(
            return_value={
                "saves_time": False,
                "works_in_real_world": True,
                "feels_personalized": False,
                "strengths": ["Budget is clear"],
                "issues": ["Feels generic", "Needs faster decision-ready summary"],
                "revision_required": True,
                "revision_instructions": ["Tighten the plan", "Make route choices reflect the user better"],
            }
        )
        self.coordinator.quality_agent.revise = Mock(return_value=revised_context)

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["planner_brief"], "Revised to be faster, more practical, and more personal.")
        self.coordinator.quality_agent.revise.assert_called_once()

    def test_quality_gate_failure_does_not_break_plan_generation(self):
        self.configure_fresh_pipeline()
        self.coordinator.quality_agent.assess = Mock(side_effect=RuntimeError("quality service failed"))

        result = self.coordinator.run("plan my trip to Jaipur")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generation_mode"], "fresh_plan")
        self.assertEqual(result.get("quality_report", {}), {})
        self.assertTrue(any("QualityAgent skipped" in step for step in result["pipeline_log"]))


if __name__ == "__main__":
    unittest.main()
