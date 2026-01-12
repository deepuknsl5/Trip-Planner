import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from llm.openai_client import call_openai

T = TypeVar("T", bound=BaseModel)


def clean_json_string(text: str) -> str:
    text = re.sub(r"```(?:json)?\s*(.*?)```", r"\1", text, flags=re.DOTALL)
    return text.strip()


def convert_to_model(input_text: str, target_model: Type[T]) -> T:
    schema = json.dumps(target_model.model_json_schema(), indent=2)

    system_prompt = (
        "You are a strict JSON generator.\n"
        "Return ONLY valid JSON matching the schema.\n"
        "No markdown. No explanations."
    )

    user_prompt = f"""
SCHEMA:
{schema}

INPUT:
{input_text}
"""

    raw = call_openai(system_prompt, user_prompt, temperature=0)
    cleaned = clean_json_string(raw)

    parsed = json.loads(cleaned)
    return target_model.model_validate(parsed)
