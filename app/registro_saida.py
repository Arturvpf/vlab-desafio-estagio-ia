from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .llm import LLMResult
from .prompt_engineer import StudentProfile


OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


def _stable_slug(text: str, *, max_len: int = 48) -> str:
    """Cria um slug simples e estável para nomes de arquivo."""
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-]+", "", text)
    text = re.sub(r"\-+", "-", text).strip("-")
    if not text:
        return "topico"
    return text[:max_len]


def _now_ts() -> int:
    return int(time.time())


def _now_iso() -> str:
    # ISO-8601 simples em UTC
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass(frozen=True)
class OutputRecord:
    """Registro persistido no diretório outputs/.

    Mantemos campos úteis para depurar e comparar versões de prompt na prática.
    """

    run_id: str
    created_at_unix: int
    created_at_iso: str

    topic: str
    kind: str  # concept|examples|reflection|visual
    prompt_version: str

    student: dict[str, Any]

    provider: str | None
    model: str | None
    latency_ms: int | None

    cache_hit: bool
    cache_key: str

    diagnostico: dict[str, Any]

    content: str


def build_record(
    *,
    topic: str,
    kind: str,
    prompt_version: str,
    student: StudentProfile,
    content: str,
    cache_hit: bool,
    cache_key: str,
    llm: LLMResult | None,
    diagnostico: dict[str, Any] | None = None,
) -> OutputRecord:
    diag = diagnostico or {}
    diag.setdefault("content_chars", len(content or ""))

    return OutputRecord(
        run_id=str(uuid.uuid4()),
        created_at_unix=_now_ts(),
        created_at_iso=_now_iso(),
        topic=topic,
        kind=kind,
        prompt_version=prompt_version,
        student={
            "id": student.id,
            "nome": student.nome,
            "idade": student.idade,
            "nivel": student.nivel,
            "estilo": student.estilo,
            "observacoes": student.observacoes,
        },
        provider=(llm.provider if llm else None),
        model=(llm.model if llm else None),
        latency_ms=(llm.latency_ms if llm else None),
        cache_hit=cache_hit,
        cache_key=cache_key,
        diagnostico=diag,
        content=content,
    )


def save_record(record: OutputRecord, *, outputs_dir: Path | None = None) -> Path:
    """Salva o registro em outputs/ com nome informativo e único."""
    out_dir = outputs_dir or OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    topic_slug = _stable_slug(record.topic)
    student_slug = _stable_slug(record.student.get("id", "aluno"))

    fname = (
        f"{record.created_at_unix}_"
        f"{record.kind}_"
        f"{record.prompt_version}_"
        f"{student_slug}_"
        f"{topic_slug}_"
        f"{record.run_id[:8]}.json"
    )

    path = out_dir / fname
    data = asdict(record)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
