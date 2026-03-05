from __future__ import annotations

import shutil
from pathlib import Path

from dotenv import load_dotenv

from app.config import load_llm_config
from app.geracao import (
    GenerationOptions,
    gerar_exemplos_praticos,
    gerar_explicacao_conceitual,
    gerar_perguntas_reflexao,
    gerar_resumo_visual,
)
from app.perfis import get_profile


ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
SAMPLES = ROOT / "samples"


def _latest_outputs(n: int = 1) -> list[Path]:
    files = sorted(OUTPUTS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:n]


def main() -> None:
    load_dotenv(str(ROOT / ".env"))
    cfg = load_llm_config()

    # Perfis
    rafael = get_profile("Rafael_10_iniciante_visual")
    manoel = get_profile("Manoel_16_intermediario_cinestesico")

    # Limpa samples antigos gerados (mantém README.md)
    for p in SAMPLES.glob("sample_real_*.json"):
        p.unlink()

    SAMPLES.mkdir(parents=True, exist_ok=True)

    # Gera 4 tipos (v1) com tópicos diferentes para mostrar variedade
    opts = GenerationOptions(prompt_version="v1", persist_outputs=True)

    gerar_explicacao_conceitual(student=rafael, topic="Frações (introdução)", llm_cfg=cfg, opts=opts)
    p = _latest_outputs(1)[0]
    shutil.copy2(p, SAMPLES / "sample_real_concept_v1_rafael_fracoes.json")

    gerar_exemplos_praticos(student=rafael, topic="Redes neurais (introdução)", llm_cfg=cfg, opts=opts)
    p = _latest_outputs(1)[0]
    shutil.copy2(p, SAMPLES / "sample_real_examples_v1_rafael_redes_neurais.json")

    gerar_perguntas_reflexao(student=manoel, topic="Energia cinética e potencial", llm_cfg=cfg, opts=opts)
    p = _latest_outputs(1)[0]
    shutil.copy2(p, SAMPLES / "sample_real_reflection_v1_manoel_energia.json")

    gerar_resumo_visual(student=manoel, topic="Ciclo da água", llm_cfg=cfg, opts=opts)
    p = _latest_outputs(1)[0]
    shutil.copy2(p, SAMPLES / "sample_real_visual_v1_manoel_ciclo_da_agua.json")

    print("OK: samples reais gerados em samples/ (arquivos sample_real_*.json)")


if __name__ == "__main__":
    main()
