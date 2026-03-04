class LLMError(RuntimeError):
    """Base class for LLM call errors."""


class LLMAuthError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMUpstreamError(LLMError):
    pass


class LLMResponseFormatError(LLMError):
    pass
