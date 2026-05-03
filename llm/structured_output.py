import json
import re
from typing import Type, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from llm.errors import LLMError, LLMResponseError
from llm.openai_client import call_openai

T = TypeVar("T", bound=BaseModel)


def clean_json_string(text: str) -> str:
    text = re.sub(r"```(?:json)?\s*(.*?)```", r"\1", text, flags=re.DOTALL)
    return text.strip()


def convert_to_model(input_text: str, target_model: Type[T]) -> T:
    schema = json.dumps(target_model.model_json_schema(), indent=2)
    request_id = str(uuid4())

    system_prompt = (
        "You are a strict JSON generator.\n"
        "Return ONLY valid JSON matching the schema.\n"
        "If a fact is uncertain, prefer a safe estimate, generic area-level wording, or an explicit unknown over invention.\n"
        "Do not invent tool outputs, citations, ratings, opening hours, or live data.\n"
        "No markdown. No explanations."
    )

    base_user_prompt = f"""
SCHEMA:
{schema}

INPUT:
{input_text}
"""

    last_error = ""

    for attempt in range(3):
        user_prompt = base_user_prompt
        if last_error:
            user_prompt += f"""

PREVIOUS OUTPUT ERROR:
{last_error}

Fix the JSON and return it again.
"""

        try:
            raw = call_openai(
                system_prompt,
                user_prompt,
                temperature=0,
                request_id=request_id,
            )
            cleaned = clean_json_string(raw)
            parsed = json.loads(cleaned)
            return target_model.model_validate(parsed)

        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as e:
            last_error = str(e)
        except LLMError:
            raise

    raise LLMResponseError(
        f"Failed to parse LLM response after 3 attempts for request_id={request_id}. Last error: {last_error}"
    )
