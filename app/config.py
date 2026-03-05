import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    provider: str  # "gemini" | "openai" | "anthropic" | "xai"
    api_key: str
    model: str
    timeout_s: int = 30


def _env(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    return val


def load_llm_config() -> LLMConfig:
    """Carrega a configuração do LLM a partir do ambiente.

    Prioridade:
      1) GEMINI_API_KEY
      2) OPENAI_API_KEY
      3) ANTHROPIC_API_KEY
      4) XAI_API_KEY

    Lança ConfigError se nenhuma chave estiver configurada.
    """

    timeout_s = int(_env("LLM_TIMEOUT_S", "30") or "30")

    gemini_key = _env("GEMINI_API_KEY")
    if gemini_key:
        model = _env("GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"
        return LLMConfig(provider="gemini", api_key=gemini_key, model=model, timeout_s=timeout_s)

    openai_key = _env("OPENAI_API_KEY")
    if openai_key:
        model = _env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        return LLMConfig(provider="openai", api_key=openai_key, model=model, timeout_s=timeout_s)

    anthropic_key = _env("ANTHROPIC_API_KEY")
    if anthropic_key:
        model = _env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest") or "claude-3-5-sonnet-latest"
        return LLMConfig(provider="anthropic", api_key=anthropic_key, model=model, timeout_s=timeout_s)

    xai_key = _env("XAI_API_KEY")
    if xai_key:
        model = _env("XAI_MODEL", "grok-2-latest") or "grok-2-latest"
        return LLMConfig(provider="xai", api_key=xai_key, model=model, timeout_s=timeout_s)

    raise ConfigError(
        "Nenhuma API key configurada. Configure GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY ou XAI_API_KEY no .env."
    )
