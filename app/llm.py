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
        return _openai_generate(prompt, cfg)
    raise LLMUpstreamError(f"Provider desconhecido: {cfg.provider}")


def _openai_generate(prompt: str, cfg: LLMConfig) -> LLMResult:
    """Chamada simples à OpenAI (Responses API).

    Mantemos a integração minimalista e consistente com o resto do projeto.
    """

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": cfg.model,
        "input": prompt,
        # Podemos evoluir isso depois (temperature, max_output_tokens, etc.)
    }

    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=cfg.timeout_s)
    except requests.Timeout as e:
        raise LLMTimeoutError("Timeout ao chamar OpenAI") from e
    except requests.RequestException as e:
        raise LLMUpstreamError("Falha de rede ao chamar OpenAI") from e

    latency_ms = int((time.time() - start) * 1000)

    if resp.status_code in (401, 403):
        raise LLMAuthError("Falha de autenticação (verifique OPENAI_API_KEY)")
    if resp.status_code == 429:
        raise LLMRateLimitError("Rate limit / quota excedida (OpenAI)")
    if resp.status_code >= 500:
        raise LLMUpstreamError(f"Erro upstream OpenAI ({resp.status_code})")

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise LLMResponseFormatError("Resposta não-JSON da OpenAI") from e

    # Erros costumam vir como {"error": {"message": "...", ...}}
    # Se possível, devolvemos o máximo de contexto (sem vazar secrets).
    # Alguns payloads podem incluir a chave "error" mesmo em respostas OK (ex.: null).
    # Só tratamos como erro se houver conteúdo significativo.
    if isinstance(data, dict) and data.get("error"):
        err = data.get("error")

        msg = None
        etype = None
        code = None
        param = None

        if isinstance(err, dict):
            msg = err.get("message")
            etype = err.get("type")
            code = err.get("code")
            param = err.get("param")
        elif isinstance(err, str):
            msg = err

        if not msg:
            msg = "Erro retornado pela OpenAI"

        detail = msg
        if etype:
            detail += f" | type={etype}"
        if code:
            detail += f" | code={code}"
        if param:
            detail += f" | param={param}"

        raise LLMUpstreamError(f"OpenAI retornou erro ({resp.status_code}): {detail}")

    # Alguns erros vêm sem JSON no campo 'error', mas ainda com status 4xx.
    if resp.status_code >= 400:
        snippet = resp.text[:500].strip() if resp.text else ""
        raise LLMUpstreamError(f"OpenAI rejeitou a requisição ({resp.status_code}): {snippet}")

    text = _extract_openai_text(data)
    if not text.strip():
        raise LLMResponseFormatError(
            f"Formato inesperado da resposta OpenAI: não consegui extrair texto | keys={list(data.keys())}"
        )

    return LLMResult(text=text.strip(), provider="openai", model=cfg.model, latency_ms=latency_ms)


def _extract_openai_text(data: dict) -> str:
    """Extrai texto de respostas da Responses API.

    A OpenAI pode retornar o texto agregado em `output_text`, mas também pode
    estruturar em `output[]` com itens e blocos de `content[]`.
    """

    if not isinstance(data, dict):
        return ""

    # Caminho mais simples
    ot = data.get("output_text")
    if isinstance(ot, str) and ot.strip():
        return ot

    out = data.get("output")
    if not isinstance(out, list):
        return ""

    chunks: list[str] = []
    for item in out:
        if not isinstance(item, dict):
            continue

        # Alguns formatos usam item["content"] = [{"type":"output_text","text":"..."}, ...]
        content = item.get("content")
        if isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
                t = c.get("text")
                if isinstance(t, str) and t.strip():
                    chunks.append(t)

        # Fallback: às vezes pode vir em campos alternativos
        t2 = item.get("output_text")
        if isinstance(t2, str) and t2.strip():
            chunks.append(t2)

    return "\n".join(chunks).strip()


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

    # Quando a API responde com erro, normalmente vem neste formato:
    # {"error": {"message": "...", "status": "..."}}
    if isinstance(data, dict) and "error" in data:
        err = data.get("error") or {}
        msg = err.get("message") or "Erro retornado pelo Gemini"
        status = err.get("status")
        code = err.get("code")
        detail = f"{msg}"
        if status:
            detail += f" | status={status}"
        if code:
            detail += f" | code={code}"

        # 400 costuma ser: API key inválida, modelo inválido, API não habilitada, etc.
        if resp.status_code in (400, 404):
            raise LLMUpstreamError(f"Gemini rejeitou a requisição ({resp.status_code}): {detail}")
        raise LLMUpstreamError(f"Gemini retornou erro: {detail}")

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
