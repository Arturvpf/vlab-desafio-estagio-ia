from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .prompt_engineer import StudentProfile


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_profiles(path: Path | None = None) -> list[StudentProfile]:
    """Carrega perfis de alunos a partir de JSON."""
    p = path or (DATA_DIR / "student_profiles.json")
    raw = json.loads(p.read_text(encoding="utf-8"))
    profiles: list[StudentProfile] = []

    for item in raw:
        profiles.append(
            StudentProfile(
                id=item["id"],
                nome=item["nome"],
                idade=int(item["idade"]),
                nivel=item["nivel"],
                estilo=item["estilo"],
                observacoes=item.get("observacoes", "") or "",
            )
        )

    return profiles


def get_profile(profile_id: str) -> StudentProfile:
    for p in load_profiles():
        if p.id == profile_id:
            return p
    raise KeyError(f"Perfil não encontrado: {profile_id}")


def dump_profile(profile: StudentProfile) -> dict:
    return asdict(profile)
