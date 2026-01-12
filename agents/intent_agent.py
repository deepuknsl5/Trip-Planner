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

        intent: TravelIntent = convert_to_model(
            input_text=user_input,
            target_model=TravelIntent
        )

        return intent.model_dump()
