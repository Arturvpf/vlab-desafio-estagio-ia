from __future__ import annotations

from dataclasses import dataclass

from .config import LLMConfig
from .prompt_engineer import EngineResult, StudentProfile, generate_with_cache, load_template


@dataclass(frozen=True)
class GenerationOptions:
    prompt_version: str = "v1"
    cache_ttl_s: int | None = None


def gerar_explicacao_conceitual(
    *,
    student: StudentProfile,
    topic: str,
    llm_cfg: LLMConfig,
    opts: GenerationOptions | None = None,
) -> EngineResult:
    opts = opts or GenerationOptions()
    template = load_template("concept", version=opts.prompt_version)
    return generate_with_cache(
        kind="concept",
        template=template,
        student=student,
        topic=topic,
        llm_cfg=llm_cfg,
        ttl_s=opts.cache_ttl_s,
    )


def gerar_exemplos_praticos(
    *,
    student: StudentProfile,
    topic: str,
    llm_cfg: LLMConfig,
    opts: GenerationOptions | None = None,
) -> EngineResult:
    opts = opts or GenerationOptions()
    template = load_template("examples", version=opts.prompt_version)
    return generate_with_cache(
        kind="examples",
        template=template,
        student=student,
        topic=topic,
        llm_cfg=llm_cfg,
        ttl_s=opts.cache_ttl_s,
    )


def gerar_perguntas_reflexao(
    *,
    student: StudentProfile,
    topic: str,
    llm_cfg: LLMConfig,
    opts: GenerationOptions | None = None,
) -> EngineResult:
    opts = opts or GenerationOptions()
    template = load_template("reflection", version=opts.prompt_version)
    return generate_with_cache(
        kind="reflection",
        template=template,
        student=student,
        topic=topic,
        llm_cfg=llm_cfg,
        ttl_s=opts.cache_ttl_s,
    )


def gerar_resumo_visual(
    *,
    student: StudentProfile,
    topic: str,
    llm_cfg: LLMConfig,
    opts: GenerationOptions | None = None,
) -> EngineResult:
    opts = opts or GenerationOptions()
    template = load_template("visual", version=opts.prompt_version)
    return generate_with_cache(
        kind="visual",
        template=template,
        student=student,
        topic=topic,
        llm_cfg=llm_cfg,
        ttl_s=opts.cache_ttl_s,
    )
