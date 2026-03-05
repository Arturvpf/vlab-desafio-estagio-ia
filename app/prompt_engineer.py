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
        """Assinatura curta do template para participar da chave do cache."""
        txt = self.read_text()
        # remove espaços para estabilizar pequenas diferenças de indentação
        collapsed = re.sub(r"\s+", " ", txt).strip()
        return str(abs(hash(collapsed)))

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


def _clean_topic(topic: str) -> str:
    topic = (topic or "").strip()
    topic = re.sub(r"\s+", " ", topic)
    return topic


def _basic_format_guard(text: str, *, markers: tuple[str, ...]) -> None:
    """Guarda de formato bem simples.

    Não tenta avaliar qualidade, só detecta respostas claramente fora do formato.
    """
    for m in markers:
        if m not in text:
            raise LLMResponseFormatError(
                f"Resposta não contém o marcador obrigatório '{m}'. Resposta veio fora do formato."
            )


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
        return EngineResult(content=str(cached.value), llm=None, cache_hit=True, cache_key=key)

    prompt = template.render(student=student, topic=topic)
    llm_result = generate_text(prompt, llm_cfg)

    # Validação mínima do formato.
    _basic_format_guard(llm_result.text, markers=template.required_markers)

    cache_set(key, llm_result.text)
    return EngineResult(content=llm_result.text, llm=llm_result, cache_hit=False, cache_key=key)


def load_template(kind: str, version: str = "v1") -> PromptTemplate:
    """Carrega template de prompt por tipo e versão."""
    kind_map = {
        "concept": ("concept", ("TÍTULO:", "EXPLICAÇÃO")),
        "examples": ("examples", ("EXEMPLO 1", "EXEMPLO 4")),
        "reflection": ("reflection", ("PERGUNTAS", "COMO RESPONDER")),
        "visual": ("visual", ("RESUMO VISUAL",)),
    }
    if kind not in kind_map:
        raise ValueError(f"kind inválido: {kind}")

    template_id, required = kind_map[kind]
    path = PROMPTS_DIR / f"{template_id}_{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {path}")

    return PromptTemplate(template_id=template_id, version=version, path=path, required_markers=required)
