# llm/openai_client.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_openai(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    """
    Calls OpenAI and forces structured JSON output.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content