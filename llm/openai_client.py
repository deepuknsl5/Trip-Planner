# llm/openai_client.py

import json
import logging
import time
from uuid import uuid4

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from config import settings
from llm.errors import (
    LLMConfigurationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)


logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)


def _log_event(level: int, event: str, **payload) -> None:
    logger.log(level, json.dumps({"event": event, **payload}, default=str))


def _build_client() -> OpenAI:
    if not settings.openai_api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.openai_api_key, max_retries=0)


client: OpenAI | None = None


def _get_client() -> OpenAI:
    global client
    if client is None:
        client = _build_client()
    return client


def call_openai(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    request_id: str | None = None,
) -> str:
    """
    Calls OpenAI with explicit retry and timeout behavior.
    """
    request_id = request_id or str(uuid4())
    attempt_count = settings.openai_max_retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempt_count + 1):
        started_at = time.perf_counter()
        _log_event(
            logging.INFO,
            "llm_request_started",
            request_id=request_id,
            attempt=attempt,
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
        )
        try:
            response = _get_client().chat.completions.create(
                model=settings.openai_model,
                temperature=temperature,
                timeout=settings.openai_timeout_seconds,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMResponseError("OpenAI returned an empty response.")

            _log_event(
                logging.INFO,
                "llm_request_succeeded",
                request_id=request_id,
                attempt=attempt,
                latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return content

        except APITimeoutError as exc:
            last_error = LLMTimeoutError(f"OpenAI request timed out for request_id={request_id}.")
        except APIConnectionError as exc:
            last_error = LLMConnectionError(f"OpenAI connection failed for request_id={request_id}: {exc}")
        except RateLimitError as exc:
            last_error = LLMRateLimitError(f"OpenAI rate limit hit for request_id={request_id}: {exc}")
        except APIStatusError as exc:
            if exc.status_code and exc.status_code >= 500:
                last_error = LLMConnectionError(
                    f"OpenAI returned retryable status {exc.status_code} for request_id={request_id}: {exc}"
                )
            else:
                last_error = LLMResponseError(
                    f"OpenAI returned status {exc.status_code} for request_id={request_id}: {exc}"
                )
        except LLMError as exc:
            last_error = exc
        except Exception as exc:
            last_error = LLMResponseError(f"Unexpected OpenAI client failure for request_id={request_id}: {exc}")

        _log_event(
            logging.WARNING,
            "llm_request_failed",
            request_id=request_id,
            attempt=attempt,
            error_type=type(last_error).__name__ if last_error else "UnknownError",
            error=str(last_error),
            latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )

        is_retryable = isinstance(
            last_error,
            (LLMTimeoutError, LLMConnectionError, LLMRateLimitError),
        )
        if attempt < attempt_count and is_retryable:
            time.sleep(min(2 ** (attempt - 1), 4))
            continue

        if last_error is not None:
            raise last_error

    if last_error is None:
        raise LLMResponseError(f"OpenAI request failed without a captured error for request_id={request_id}.")
    raise last_error
