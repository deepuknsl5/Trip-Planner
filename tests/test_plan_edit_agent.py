import unittest
from unittest.mock import patch

from agents.plan_edit_agent import PlanEditAgent
from models.plan_edit import PlanEditIntent
from models.travel_plan import EditableTravelPlan

from tests.test_coordinator import sample_editable_plan


class PlanEditAgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = PlanEditAgent()

    @patch("agents.plan_edit_agent.convert_to_model")
    def test_detect_uses_plan_edit_schema(self, mock_convert):
        mock_convert.return_value = PlanEditIntent(
            is_plan_edit=True,
            summary="Make it cheaper",
            response_focus="budget",
            keep_destination=True,
            requested_changes=["Reduce costs"],
        )

        result = self.agent.detect("make it cheaper", {"editable_plan": sample_editable_plan()})

        self.assertTrue(result["is_plan_edit"])
        self.assertEqual(result["response_focus"], "budget")
        self.assertIs(mock_convert.call_args.kwargs["target_model"], PlanEditIntent)

    @patch("agents.plan_edit_agent.convert_to_model")
    def test_execute_recomputes_feasible_destinations_from_updated_budget(self, mock_convert):
        updated_plan = sample_editable_plan()
        updated_plan["budget_analysis"]["budget_analysis"] = [
            {
                **updated_plan["budget_analysis"]["budget_analysis"][0],
                "destination": "Jaipur, India",
                "feasibility": "feasible",
            },
            {
                **updated_plan["budget_analysis"]["budget_analysis"][0],
                "destination": "Udaipur, India",
                "feasibility": "not_feasible",
            },
        ]
        mock_convert.return_value = EditableTravelPlan.model_validate(updated_plan)

        result = self.agent.execute(
            user_input="make it cheaper",
            previous_plan=sample_editable_plan(),
            edit_intent={
                "is_plan_edit": True,
                "summary": "Make it cheaper",
                "response_focus": "budget",
                "keep_destination": True,
                "requested_changes": ["Reduce total cost"],
            },
        )

        self.assertEqual(len(result["feasible_destinations"]), 1)
        self.assertEqual(result["feasible_destinations"][0]["destination"], "Jaipur, India")
        self.assertIs(mock_convert.call_args.kwargs["target_model"], EditableTravelPlan)


if __name__ == "__main__":
    unittest.main()
