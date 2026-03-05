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

Edite `.env` com sua chave de API.

### Provedores suportados

Você pode usar **Gemini**, **OpenAI**, **Claude (Anthropic)** ou **Grok (xAI)**.

**Status de testes:** este projeto foi testado na prática apenas com **OpenAI/ChatGPT (API)**. Os outros provedores foram integrados seguindo a documentação oficial e podem exigir ajustes finos (modelos/limites) dependendo da sua conta.

**Gemini (Google AI Studio):**
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (ex.: `gemini-2.0-flash-lite`)

**OpenAI:**
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (recomendado: `gpt-4o-mini`)

**Claude (Anthropic):**
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL` (ex.: `claude-3-5-sonnet-latest`)

**Grok (xAI):**
- `XAI_API_KEY`
- `XAI_MODEL` (ex.: `grok-2-latest`)

> Observação: o app seleciona o provedor automaticamente pela primeira chave encontrada (ordem: Gemini → OpenAI → Anthropic → xAI).

## Rodar

```bash
python3 -m app
```

Acesse: http://127.0.0.1:5000

## Estrutura
- `docs/` — enunciado do desafio (PDF)
- `app/` — aplicação Flask
- `data/student_profiles.json` — perfis (3–5)
- `prompts/` — versões de prompts
- `outputs/` — gerações salvas (JSON)
- `samples/` — exemplos de output JSON para entrega
- `cache/` — cache local
- `PROMPT_ENGINEERING_NOTES.md` — notas de engenharia de prompt

## Como usar (web)
1) Inicie o servidor com `python3 -m app`
2) Selecione um aluno
3) Escolha o tipo de conteúdo e a versão do prompt
4) Digite um tópico e clique em **Gerar**

A aplicação:
- usa cache para evitar chamadas repetidas
- salva automaticamente a saída em `outputs/` (JSON)

## Observação sobre chain-of-thought
O sistema pede ao modelo para **raciocinar passo a passo internamente**, mas **não** salva/retorna o raciocínio detalhado. Ele retorna uma explicação clara e estruturada.
