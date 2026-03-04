import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    provider: str  # "gemini" | "openai" (futuro)
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
      2) OPENAI_API_KEY (placeholder para depois)

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

    raise ConfigError(
        "Nenhuma API key configurada. Configure GEMINI_API_KEY (recomendado) ou OPENAI_API_KEY no .env."
    )
