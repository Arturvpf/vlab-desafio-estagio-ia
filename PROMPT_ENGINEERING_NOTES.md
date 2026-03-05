# Prompt Engineering Notes

Este projeto gera conteúdo educacional personalizado a partir de perfis de aluno.

A filosofia aqui é **prática**: prompts com formato previsível, cache para economizar chamadas e um "motor" que corta ruído (ex.: frases de abertura) para manter a saída sempre limpa.

## Estrutura de prompts

Cada tipo de conteúdo tem seu próprio arquivo em `prompts/` e duas versões:
- `*_v1.txt` — **Estruturado** (mais direto e linear)
- `*_v2.txt` — **Trilha + checkpoints** (mesma ideia, mas com organização mais guiada e verificações)

Os prompts seguem um padrão:
- **ENTRADAS** (perfil do aluno + tópico)
- **REGRAS** (adequação pedagógica + restrições)
- **SAÍDA (formato obrigatório)** (seções com marcadores estáveis)

Os marcadores (ex.: `TÍTULO`, `EXPLICAÇÃO`, `PERGUNTAS`, `RESUMO VISUAL`, `LIÇÃO`) foram escolhidos para:
- forçar consistência
- permitir validação mínima de formato no código
- facilitar comparação entre versões

## Técnicas usadas

### 1) Persona prompting
Os prompts fixam o papel do modelo como professor(a)/designer instrucional.
Isso ajuda a evitar respostas “genéricas” e mantém o foco em didática.

### 2) Context setting (perfil do aluno)
O prompt inclui:
- idade
- nível (iniciante / intermediário / avançado)
- estilo (visual / auditivo / leitura-escrita / cinestésico)
- observações (curtas)

Isso direciona vocabulário, tipo de exemplo e profundidade.

### 3) Chain-of-thought (raciocínio interno)
O enunciado pede “pense passo a passo”. Para seguir boas práticas:
- permitimos organização interna
- **não** pedimos nem exibimos o raciocínio detalhado
- a saída final é sempre estruturada

### 4) Output formatting (formato de saída)
Cada tipo exige um formato próprio.
Na prática, isso reduz alucinação de estrutura (ex.: parágrafos soltos) e melhora a reutilização do conteúdo.

## Medidas práticas para robustez

### 1) Corte de frase de abertura
Alguns modelos adicionam “Claro! Aqui está…”.
O motor remove qualquer texto antes do primeiro marcador relevante, garantindo que o output fique “limpo” (inclusive no JSON e na UI).

### 2) Validação mínima (case-insensitive)
O motor checa a presença de marcadores essenciais (ex.: `PERGUNTAS`) sem depender de maiúsculas/minúsculas.

### 3) Cache
A chave do cache inclui:
- tipo de conteúdo + versão do prompt
- fingerprint do prompt (sha256 do arquivo)
- perfil do aluno
- tópico
- provider/model

Assim, mudar o texto do prompt muda automaticamente a chave e evita cache “enganoso”.

## Comparação entre versões

O projeto suporta duas versões por tipo (v1/v2). A comparação é feita gerando as duas e registrando outputs com metadados (timestamp, modelo, cache hit/miss etc.).

Critérios práticos para comparar:
- aderência ao perfil (idade/nível/estilo)
- clareza e estrutura
- exemplos realmente contextualizados
- ausência de “ruídos” (frases fora do formato)
