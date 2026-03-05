from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cache import CacheHit, CacheMiss, get as cache_get, make_cache_key, set as cache_set
from .config import LLMConfig
from .errors import LLMResponseFormatError
from .llm import LLMResult, generate_text


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass(frozen=True)
class StudentProfile:
    id: str
    nome: str
    idade: int
    nivel: str
    estilo: str
    observacoes: str = ""


@dataclass(frozen=True)
class PromptTemplate:
    """Template de prompt + metadados mínimos.

    A ideia é manter os prompts como arquivos .txt (versão controlada) e
    tornar o código só o "motor" que injeta contexto e valida formato.
    """

    template_id: str  # ex: "concept"
    version: str  # ex: "v1"
    path: Path
    required_markers: tuple[str, ...]

    def read_text(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def fingerprint(self) -> str:
        """Assinatura estável do template para participar da chave do cache.

        Usamos sha256 do conteúdo do arquivo para evitar variação entre execuções.
        """
        import hashlib

        txt = self.read_text().encode("utf-8")
        return hashlib.sha256(txt).hexdigest()[:16]

    def render(self, *, student: StudentProfile, topic: str) -> str:
        raw = self.read_text()
        mapping: dict[str, Any] = {
            "student_id": student.id,
            "student_name": student.nome,
            "student_age": student.idade,
            "student_level": student.nivel,
            "student_style": student.estilo,
            "student_notes": student.observacoes,
            "topic": topic,
        }

        try:
            prompt = raw.format(**mapping)
        except KeyError as e:
            raise RuntimeError(f"Placeholder ausente no template: {e}") from e

        # Validação simples: garantir que o template contém marcadores essenciais.
        for marker in self.required_markers:
            if marker not in prompt:
                raise RuntimeError(
                    f"Template renderizado perdeu marcador obrigatório '{marker}' ({self.path.name})"
                )
        return prompt


@dataclass(frozen=True)
class EngineResult:
    content: str
    llm: LLMResult | None
    cache_hit: bool
    cache_key: str
    meta: dict[str, Any]


def _clean_topic(topic: str) -> str:
    topic = (topic or "").strip()
    topic = re.sub(r"\s+", " ", topic)
    return topic


def _basic_format_guard(text: str, *, markers: tuple[str, ...]) -> None:
    """Guarda de formato (prática, não acadêmica).

    Objetivo: falhar rápido quando o modelo ignora o formato combinado.
    Não valida 'qualidade', só estrutura mínima.

    Observação: a checagem é case-insensitive para tolerar "Perguntas" vs "PERGUNTAS".
    """

    hay = (text or "")
    hay_u = hay.upper()

    for m in markers:
        if (m or "").upper() not in hay_u:
            raise LLMResponseFormatError(f"Resposta fora do formato: não encontrei '{m}'.")

    # Heurística extra: evitar respostas vazias/curtíssimas
    if len(hay.strip()) < 80:
        raise LLMResponseFormatError("Resposta curta demais; provável falha de geração/formato.")


def _trim_to_first_marker(text: str, markers: tuple[str, ...]) -> str:
    """Remove qualquer texto antes do primeiro marcador (case-insensitive).

    Útil quando o modelo adiciona uma frase de abertura ("Claro! ...") e isso
    não deve aparecer na saída final.
    """
    if not text:
        return text

    text_u = text.upper()
    idxs: list[int] = []
    for m in markers:
        mu = (m or "").upper()
        if not mu:
            continue
        i = text_u.find(mu)
        if i != -1:
            idxs.append(i)

    if not idxs:
        return text

    start = min(idxs)
    return text[start:].lstrip()


def generate_with_cache(
    *,
    kind: str,
    template: PromptTemplate,
    student: StudentProfile,
    topic: str,
    llm_cfg: LLMConfig,
    ttl_s: int | None = None,
) -> EngineResult:
    """Gera conteúdo para um tipo (kind) com cache.

    kind: "concept" | "examples" | "reflection" | "visual"
    """

    topic = _clean_topic(topic)

    cache_payload = {
        "kind": kind,
        "template_id": template.template_id,
        "template_version": template.version,
        "template_fp": template.fingerprint(),
        "student": {
            "id": student.id,
            "idade": student.idade,
            "nivel": student.nivel,
            "estilo": student.estilo,
            # 'nome' e 'observacoes' influenciam tom; incluímos para evitar reuse incorreto
            "nome": student.nome,
            "observacoes": student.observacoes,
        },
        "topic": topic,
        "provider": llm_cfg.provider,
        "model": llm_cfg.model,
    }

    key = make_cache_key(payload=cache_payload)
    cached = cache_get(key, ttl_s=ttl_s)
    if isinstance(cached, CacheHit):
        return EngineResult(
            content=str(cached.value),
            llm=None,
            cache_hit=True,
            cache_key=key,
            meta={
                "template": {
                    "id": template.template_id,
                    "version": template.version,
                    "fingerprint": template.fingerprint(),
                    "file": template.path.name,
                },
                "kind": kind,
                "topic": topic,
            },
        )

    prompt = template.render(student=student, topic=topic)
    llm_result = generate_text(prompt, llm_cfg)

    # Pós-processo: cortar frase de abertura antes do primeiro marcador.
    cleaned = _trim_to_first_marker(llm_result.text, template.required_markers)

    # Validação mínima do formato.
    _basic_format_guard(cleaned, markers=template.required_markers)

    cache_set(key, cleaned)
    return EngineResult(
        content=cleaned,
        llm=llm_result,
        cache_hit=False,
        cache_key=key,
        meta={
            "template": {
                "id": template.template_id,
                "version": template.version,
                "fingerprint": template.fingerprint(),
                "file": template.path.name,
            },
            "kind": kind,
            "topic": topic,
            "prompt_chars": len(prompt),
            "output_chars": len(llm_result.text),
        },
    )


def load_template(kind: str, version: str = "v1") -> PromptTemplate:
    """Carrega template de prompt por tipo e versão."""
    kind_map = {
        # marcadores usados como "sinalizadores" do formato
        "concept": ("concept", ("TÍTULO", "EXPLICAÇÃO")),
        "examples": ("examples", ("EXEMPLO", "LIÇÃO")),
        "reflection": ("reflection", ("PERGUNTAS",)),
        "visual": ("visual", ("RESUMO VISUAL",)),
    }
    if kind not in kind_map:
        raise ValueError(f"kind inválido: {kind}")

    template_id, required = kind_map[kind]
    path = PROMPTS_DIR / f"{template_id}_{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {path}")

    return PromptTemplate(template_id=template_id, version=version, path=path, required_markers=required)
