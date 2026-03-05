from __future__ import annotations

from dataclasses import asdict

from flask import Flask, redirect, render_template_string, request, url_for
from dotenv import load_dotenv

from .comparacao_prompts import comparar_duas_versoes
from .config import ConfigError, load_llm_config
from .geracao import (
    GenerationOptions,
    gerar_exemplos_praticos,
    gerar_explicacao_conceitual,
    gerar_perguntas_reflexao,
    gerar_resumo_visual,
)
from .perfis import get_profile, load_profiles


HTML = """<!doctype html>
<html lang=\"pt-br\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>VLAB — Gerador Educativo</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; max-width: 980px; }
    .row { display: flex; gap: 16px; flex-wrap: wrap; }
    .card { border: 1px solid #e5e5e5; border-radius: 10px; padding: 16px; }
    label { display:block; font-weight:600; margin-top: 10px; }
    select, input[type=text], textarea { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc; }
    textarea { min-height: 90px; }
    button { padding: 10px 14px; border: 0; border-radius: 10px; background: #111; color: #fff; cursor: pointer; }
    .muted { color: #666; font-size: 0.95em; }
    pre { white-space: pre-wrap; background: #0b1020; color: #e8e8e8; padding: 14px; border-radius: 10px; overflow:auto; }
    .warn { background: #fff4e5; border: 1px solid #ffd9a8; padding: 12px; border-radius: 10px; }
  </style>
</head>
<body>
  <h1>VLAB — Gerador Educativo</h1>
  <p class=\"muted\">Selecione um perfil, escreva um tópico e gere o conteúdo (com cache + persistência em JSON).</p>

  {% if error %}
    <div class=\"warn\"><strong>Erro:</strong> {{ error }}</div>
  {% endif %}

  <div class=\"card\">
    <form method=\"post\" action=\"{{ url_for('gerar') }}\">
      <div class=\"row\">
        <div style=\"flex: 1 1 280px\">
          <label>Aluno</label>
          <select name=\"profile_id\" required>
            {% for p in profiles %}
              <option value=\"{{ p.id }}\" {% if p.id == selected.profile_id %}selected{% endif %}>
                {{ p.nome }} ({{ p.idade }}y, {{ p.nivel }}, {{ p.estilo }})
              </option>
            {% endfor %}
          </select>
        </div>

        <div style=\"flex: 1 1 220px\">
          <label>Tipo</label>
          <select name=\"kind\" required>
            <option value=\"concept\" {% if selected.kind=='concept' %}selected{% endif %}>Explicação conceitual</option>
            <option value=\"examples\" {% if selected.kind=='examples' %}selected{% endif %}>Exemplos práticos</option>
            <option value=\"reflection\" {% if selected.kind=='reflection' %}selected{% endif %}>Perguntas de reflexão</option>
            <option value=\"visual\" {% if selected.kind=='visual' %}selected{% endif %}>Resumo visual</option>
          </select>
        </div>

        <div style=\"flex: 1 1 140px\">
          <label>Versão</label>
          <select name=\"prompt_version\" required>
            <option value=\"v1\" {% if selected.prompt_version=='v1' %}selected{% endif %}>v1</option>
            <option value=\"v2\" {% if selected.prompt_version=='v2' %}selected{% endif %}>v2</option>
          </select>
          <label style=\"margin-top:10px; font-weight:500\">
            <input type=\"checkbox\" name=\"compare\" value=\"1\" {% if selected.compare %}checked{% endif %} />
            Comparar v1 vs v2
          </label>
        </div>
      </div>

      <label>Tópico</label>
      <input type=\"text\" name=\"topic\" placeholder=\"Ex.: Frações, Fotossíntese, Redes neurais, ...\" value=\"{{ selected.topic }}\" required />

      <div style=\"margin-top:14px\">
        <button type=\"submit\">Gerar</button>
      </div>
    </form>
  </div>

  {% if result %}
    <h2 style=\"margin-top: 22px\">Resultado</h2>
    <div class=\"card\">
      <p class=\"muted\">
        <strong>kind:</strong> {{ result.kind }} |
        <strong>versão:</strong> {{ result.prompt_version }} |
        <strong>cache_hit:</strong> {{ result.cache_hit }} |
        <strong>cache_key:</strong> {{ result.cache_key }}
      </p>
      <pre>{{ result.content }}</pre>
      <p class=\"muted\">Saída salva automaticamente em <code>outputs/</code> (JSON).</p>
    </div>
  {% endif %}

  {% if comparison %}
    <h2 style=\"margin-top: 22px\">Comparação</h2>
    <div class=\"card\">
      <p class=\"muted\">Arquivo salvo: <code>{{ comparison.path }}</code></p>
      <p class=\"muted\">Abra o JSON para ver v1 e v2 lado a lado.</p>
    </div>
  {% endif %}

  <hr style=\"margin: 24px 0\" />
  <p class=\"muted\">Dica: configure <code>.env</code> com <code>GEMINI_API_KEY</code> e rode <code>python3 -m app</code>.</p>
</body>
</html>"""


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)

    @app.get("/")
    def index():
        profiles = load_profiles()
        selected = {
            "profile_id": profiles[0].id if profiles else "",
            "kind": "concept",
            "prompt_version": "v1",
            "topic": "",
            "compare": False,
        }
        return render_template_string(HTML, profiles=profiles, selected=selected, result=None, comparison=None)

    @app.post("/gerar")
    def gerar():
        profiles = load_profiles()

        selected = {
            "profile_id": request.form.get("profile_id", ""),
            "kind": request.form.get("kind", "concept"),
            "prompt_version": request.form.get("prompt_version", "v1"),
            "topic": request.form.get("topic", "").strip(),
            "compare": request.form.get("compare") == "1",
        }

        try:
            cfg = load_llm_config()
        except ConfigError as e:
            return render_template_string(
                HTML, profiles=profiles, selected=selected, error=str(e), result=None, comparison=None
            )

        student = get_profile(selected["profile_id"])
        kind = selected["kind"]
        topic = selected["topic"]

        fn_map = {
            "concept": gerar_explicacao_conceitual,
            "examples": gerar_exemplos_praticos,
            "reflection": gerar_perguntas_reflexao,
            "visual": gerar_resumo_visual,
        }
        if kind not in fn_map:
            return render_template_string(
                HTML,
                profiles=profiles,
                selected=selected,
                error=f"kind inválido: {kind}",
                result=None,
                comparison=None,
            )

        comparison = None
        if selected["compare"]:
            # comparação gera arquivo próprio; não precisa renderizar os dois textos na tela
            comparison = comparar_duas_versoes(kind=kind, topic=topic, student=student, llm_cfg=cfg, gerar_fn=fn_map[kind])
            result = None
        else:
            opts = GenerationOptions(prompt_version=selected["prompt_version"], persist_outputs=True)
            r = fn_map[kind](student=student, topic=topic, llm_cfg=cfg, opts=opts)
            result = {
                "kind": kind,
                "prompt_version": selected["prompt_version"],
                "cache_hit": r.cache_hit,
                "cache_key": r.cache_key,
                "content": r.content,
            }

        return render_template_string(
            HTML,
            profiles=profiles,
            selected=selected,
            error=None,
            result=result,
            comparison=comparison,
        )

    return app
