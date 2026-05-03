import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def _get_backend_url() -> str:
    explicit_url = os.getenv("BACKEND_URL")
    if explicit_url:
        return explicit_url

    backend_hostport = os.getenv("BACKEND_HOSTPORT")
    if backend_hostport:
        return f"http://{backend_hostport}/plan-trip"

    return "http://localhost:8000/plan-trip"


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    openai_timeout_seconds: float = _get_float("OPENAI_TIMEOUT_SECONDS", 30.0)
    openai_max_retries: int = _get_int("OPENAI_MAX_RETRIES", 2)
    backend_url: str = _get_backend_url()
    backend_timeout_seconds: float = _get_float("BACKEND_TIMEOUT_SECONDS", 180.0)
    allow_local_coordinator_fallback: bool = _get_bool(
        "ALLOW_LOCAL_COORDINATOR_FALLBACK",
        False,
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
