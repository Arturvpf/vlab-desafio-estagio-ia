# Prompt Engineering Notes

Este projeto implementa geração de conteúdo educacional personalizado a partir de perfis de aluno.

## Técnicas usadas

### 1) Persona Prompting
- **v1:** professor experiente em Pedagogia/didática
- **v2:** professor + designer instrucional com foco em aprendizagem ativa

O objetivo é estabilizar o estilo de resposta e priorizar clareza pedagógica.

### 2) Context Setting (perfil do aluno)
O prompt inclui explicitamente:
- idade
- nível (iniciante / intermediário / avançado)
- estilo (visual / auditivo / leitura-escrita / cinestésico)
- descrição curta

Isso força o modelo a escolher exemplos e linguagem adequados.

### 3) Chain-of-thought (raciocínio interno)
O enunciado pede “pense passo a passo”. Para manter boas práticas:
- Pedimos ao modelo para **raciocinar internamente**.
- A resposta entregue é **apenas o resultado final estruturado**, sem expor o raciocínio interno.

### 4) Output formatting
Cada tipo de conteúdo tem instruções específicas e **formatos diferentes** por versão:
- v1: estrutura textual clara e repetível
- v2: estrutura mais “programática” (campos/itens) para facilitar comparação

## Comparação entre versões
A aplicação permite selecionar uma versão (v1/v2) e gerar o mesmo conteúdo.
Os outputs são salvos com:
- perfil
- tópico
- versão do prompt
- tipo de conteúdo
- timestamp

Isso permite comparar qualidade posteriormente (ex.: clareza, aderência ao perfil, completude).
