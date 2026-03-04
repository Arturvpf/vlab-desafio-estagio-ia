from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_VERSION = 1


@dataclass(frozen=True)
class CacheHit:
    key: str
    path: str
    created_at: int
    value: Any


@dataclass(frozen=True)
class CacheMiss:
    key: str


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def make_cache_key(*, payload: dict) -> str:
    """Calcula uma chave de cache estável a partir de um payload (dict)."""
    raw = _stable_json({"v": CACHE_VERSION, "payload": payload})
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get(key: str, *, ttl_s: int | None = None) -> CacheHit | CacheMiss:
    """Lê uma entrada do cache, se disponível.

    ttl_s: se informado, entradas mais antigas que o TTL são tratadas como miss.
    """
    p = cache_path(key)
    if not p.exists():
        return CacheMiss(key=key)

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # Cache corrompido -> tratar como miss
        return CacheMiss(key=key)

    created_at = int(data.get("created_at") or 0)
    if ttl_s is not None and created_at:
        if int(time.time()) - created_at > ttl_s:
            return CacheMiss(key=key)

    return CacheHit(key=key, path=str(p), created_at=created_at, value=data.get("value"))


def set(key: str, value: Any) -> str:
    """Grava uma entrada no cache e retorna o caminho do arquivo."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    p = cache_path(key)
    tmp = p.with_suffix(".tmp")

    payload = {
        "cache_version": CACHE_VERSION,
        "created_at": int(time.time()),
        "value": value,
    }

    tmp.write_text(_stable_json(payload), encoding="utf-8")
    os.replace(tmp, p)
    return str(p)
