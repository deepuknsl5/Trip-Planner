class LLMError(Exception):
    """Base exception for LLM client failures."""


class LLMConfigurationError(LLMError):
    """Raised when the LLM client is misconfigured."""


class LLMConnectionError(LLMError):
    """Raised when the LLM service cannot be reached."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM service times out."""


class LLMRateLimitError(LLMError):
    """Raised when the LLM service rate-limits requests."""


class LLMResponseError(LLMError):
    """Raised when the LLM service returns an invalid or unusable response."""
