# Samples

Este diretório contém exemplos de saída em JSON.

## Samples reais (gerados via app)
- `sample_real_concept_v1_redes_neurais_rafael.json`
- `sample_real_examples_v1_redes_neurais_rafael.json`
- `sample_real_visual_v1_redes_neurais_rafael.json`
- `sample_real_reflection_v2_redes_neurais_rafael.json`

## Sample ilustrativo (estrutura)
- `sample_concept_v1_ana_fracoes.json` é um **exemplo de estrutura** (conteúdo ilustrativo).

## Como gerar mais samples reais
1) Configure `.env` com sua chave (Gemini ou OpenAI)
2) Rode `python3 -m app`
3) Gere conteúdos pela interface web
4) Copie arquivos de `outputs/` para `samples/`

> Observação: manter `samples/` com outputs reais ajuda na avaliação do desafio.
