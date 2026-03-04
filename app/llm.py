from __future__ import annotations

import json
import time
from dataclasses import dataclass

import requests

from .config import LLMConfig
from .errors import (
    LLMAuthError,
    LLMRateLimitError,
    LLMResponseFormatError,
    LLMTimeoutError,
    LLMUpstreamError,
)


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: int


def generate_text(prompt: str, cfg: LLMConfig) -> LLMResult:
    """Gera texto usando o provedor configurado.

    Retorna um resultado normalizado com provider/model/latency.
    """
    if cfg.provider == "gemini":
        return _gemini_generate(prompt, cfg)
    if cfg.provider == "openai":
        raise LLMUpstreamError(
            "Provider 'openai' ainda não implementado neste projeto. Use GEMINI_API_KEY por enquanto."
        )
    raise LLMUpstreamError(f"Provider desconhecido: {cfg.provider}")


def _gemini_generate(prompt: str, cfg: LLMConfig) -> LLMResult:
    # Usando a API Generative Language (Gemini) do Google AI Studio.
    # Documentação: https://ai.google.dev/gemini-api/docs
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.model}:generateContent"
        f"?key={cfg.api_key}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        # Mantemos o payload mínimo; podemos adicionar temperature/top_p depois.
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=cfg.timeout_s)
    except requests.Timeout as e:
        raise LLMTimeoutError("Timeout ao chamar Gemini") from e
    except requests.RequestException as e:
        raise LLMUpstreamError("Falha de rede ao chamar Gemini") from e

    latency_ms = int((time.time() - start) * 1000)

    if resp.status_code in (401, 403):
        raise LLMAuthError("Falha de autenticação (verifique GEMINI_API_KEY)")
    if resp.status_code == 429:
        raise LLMRateLimitError("Rate limit / quota excedida")
    if resp.status_code >= 500:
        raise LLMUpstreamError(f"Erro upstream Gemini ({resp.status_code})")

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise LLMResponseFormatError("Resposta não-JSON do Gemini") from e

    # Formato esperado: { candidates: [ { content: { parts: [ {text} ] } } ] }
    try:
        candidates = data.get("candidates") or []
        if not candidates:
            raise KeyError("candidates vazio")
        parts = candidates[0]["content"]["parts"]
        if not parts:
            raise KeyError("parts vazio")
        text = parts[0].get("text")
        if not isinstance(text, str) or not text.strip():
            raise KeyError("text ausente")
    except Exception as e:
        raise LLMResponseFormatError(
            f"Formato inesperado da resposta Gemini: {str(e)} | raw keys={list(data.keys())}"
        ) from e

    return LLMResult(text=text.strip(), provider="gemini", model=cfg.model, latency_ms=latency_ms)
