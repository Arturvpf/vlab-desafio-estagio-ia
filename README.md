# Desafio Técnico — Estágio em IA e Engenharia de Prompt (VLAB)

Plataforma educativa simples (Web) que gera conteúdo personalizado para alunos a partir de um **perfil** (idade, nível e estilo de aprendizado) e um **tópico**.

A aplicação gera 4 tipos de conteúdo:
1. **Explicação conceitual** (com orientação de raciocínio passo a passo *interno*, retornando apenas resposta final)
2. **Exemplos práticos** (contextualizados)
3. **Perguntas de reflexão**
4. **Resumo visual** (ASCII / descrição de diagrama)

Também suporta **versões de prompts** para comparar resultados, **cache** para evitar chamadas repetidas e **persistência** em JSON com timestamp.

## Requisitos
- Python 3.10+
- Uma API key de LLM (free-tier). Recomendado: **Google Gemini**.

## Setup

Em Ubuntu/Debian, talvez seja necessário instalar venv:

```bash
sudo apt install -y python3-venv
```

Depois:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` com sua(s) chave(s).

## Rodar

```bash
python -m app
```

Acesse: http://127.0.0.1:5000

## Estrutura
- `docs/` — enunciado do desafio (PDF)
- `app/` — aplicação Flask
- `data/student_profiles.json` — perfis (3–5)
- `prompts/` — versões de prompts
- `outputs/` — gerações salvas (JSON)
- `samples/` — exemplos de output para entrega
- `cache/` — cache local
- `PROMPT_ENGINEERING_NOTES.md` — notas de engenharia de prompt

## Observação sobre chain-of-thought
O sistema pede ao modelo para **raciocinar passo a passo internamente**, mas **não** salva/retorna o raciocínio detalhado. Ele retorna uma explicação clara e estruturada.
