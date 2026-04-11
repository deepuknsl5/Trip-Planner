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

        IMPORTANT:
        - Identify starting location (origin)
        - Identify destination if explicitly mentioned
        - Identify country if implied
        - If user says "Himachal", map to India
        - If user mentions "from Delhi", capture origin

        USER INPUT:
        {user_input}
        """

        intent: TravelIntent = convert_to_model(
            input_text=prompt,
            target_model=TravelIntent
        )

        return intent.model_dump()
