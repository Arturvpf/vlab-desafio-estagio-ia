from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import LLMConfig
from .perfis import StudentProfile
from .registro_saida import OUTPUTS_DIR, build_record


@dataclass(frozen=True)
class ComparacaoResultado:
    kind: str
    topic: str
    profile_id: str
    path: str


def _save_comparison(payload: dict, *, out_dir: Path | None = None) -> Path:
    out = out_dir or OUTPUTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    # nome simples e único
    import time, uuid

    ts = int(time.time())
    rid = str(uuid.uuid4())[:8]
    path = out / f"{ts}_compare_{payload['kind']}_{rid}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def comparar_duas_versoes(
    *,
    kind: str,
    topic: str,
    student: StudentProfile,
    llm_cfg: LLMConfig,
    gerar_fn,
) -> ComparacaoResultado:
    """Gera o mesmo conteúdo em duas versões de prompt (v1 e v2).

    Em vez de salvar dois arquivos separados, persistimos um único JSON com as
    duas versões lado a lado + metadados úteis.
    """

    from .geracao import GenerationOptions

    # Não persistir automaticamente em outputs/ aqui; a comparação já salva um arquivo próprio.
    o1 = GenerationOptions(prompt_version="v1", persist_outputs=False)
    o2 = GenerationOptions(prompt_version="v2", persist_outputs=False)

    r1 = gerar_fn(student=student, topic=topic, llm_cfg=llm_cfg, opts=o1)
    r2 = gerar_fn(student=student, topic=topic, llm_cfg=llm_cfg, opts=o2)

    rec1 = build_record(
        topic=topic,
        kind=kind,
        prompt_version="v1",
        student=student,
        content=r1.content,
        cache_hit=r1.cache_hit,
        cache_key=r1.cache_key,
        llm=r1.llm,
        diagnostico=r1.meta,
    )
    rec2 = build_record(
        topic=topic,
        kind=kind,
        prompt_version="v2",
        student=student,
        content=r2.content,
        cache_hit=r2.cache_hit,
        cache_key=r2.cache_key,
        llm=r2.llm,
        diagnostico=r2.meta,
    )

    payload = {
        "kind": kind,
        "topic": topic,
        "student": rec1.student,
        "provider": {"provider": llm_cfg.provider, "model": llm_cfg.model},
        "versions": {
            "v1": asdict(rec1),
            "v2": asdict(rec2),
        },
        "quick_compare": {
            # heurísticas simples e práticas
            "v1_chars": len(r1.content),
            "v2_chars": len(r2.content),
            "v1_cache_hit": r1.cache_hit,
            "v2_cache_hit": r2.cache_hit,
        },
    }

    path = _save_comparison(payload)

    return ComparacaoResultado(kind=kind, topic=topic, profile_id=student.id, path=str(path))
