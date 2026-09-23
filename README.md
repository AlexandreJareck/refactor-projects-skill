# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.

## Análise Manual

Esta análise foi feita sobre o código original, antes da criação e execução da skill. Os caminhos e linhas abaixo se referem ao commit inicial `6d1ce62`.

### Projeto 1 — `code-smells-project`

Stack: Python, Flask 3.1.1, Flask-CORS 5.0.1 e SQLite. Domínio: API de loja com produtos, usuários, pedidos e relatório de vendas. A aplicação concentra quatro domínios em `app.py`, `controllers.py`, `models.py` e `database.py`.

| ID | Severidade | Evidência | Impacto |
|---|---|---|---|
| P1-01 | CRITICAL | `app.py:59-69` executa SQL recebido no corpo HTTP de `/admin/query`, sem autenticação. | Qualquer cliente pode ler ou modificar todo o banco. |
| P1-02 | CRITICAL | `models.py:122-128` armazena a senha recebida sem hash; `models.py:79-85` a inclui na listagem de usuários. | Credenciais ficam expostas no banco e na API. |
| P1-03 | MEDIUM | `models.py:174-192` consulta itens e produtos dentro do loop de pedidos. | O número de consultas cresce com cada pedido e item (N+1). |
| P1-04 | MEDIUM | `controllers.py:24-54` e `controllers.py:64-90` repetem validações de produto. | Regras divergentes surgem com facilidade; a atualização já omite a validação de categoria. |
| P1-05 | LOW | `controllers.py:8-12` mistura `print` de diagnóstico com resposta HTTP. | Logs não são estruturados e sua leitura/manutenção fica difícil. |
| P1-06 | LOW | `controllers.py:52-54` embute a lista de categorias válidas diretamente no endpoint. | O valor de domínio fica disperso e é difícil manter consistente. |

### Projeto 2 — `ecommerce-api-legacy`

Stack: Node.js, Express `^4.18.2` declarado e 4.22.1 instalado pelo lockfile, com SQLite em memória. Domínio: LMS com checkout, matrículas, pagamentos e relatório financeiro. Os três endpoints estão concentrados em `src/AppManager.js`; exemplos de chamadas constam em `api.http`.

| ID | Severidade | Evidência | Impacto |
|---|---|---|---|
| P2-01 | CRITICAL | `src/AppManager.js:45` imprime número integral do cartão e chave de pagamento no log. | Dados sensíveis podem vazar pelos logs. |
| P2-02 | CRITICAL | `src/AppManager.js:4-139` reúne inicialização do banco, acesso a dados, checkout, relatório e rotas. | A classe viola completamente a separação de responsabilidades, conforme o exemplo de God Class do enunciado. |
| P2-03 | MEDIUM | `src/AppManager.js:89-106` consulta matrículas, usuários e pagamentos em loops aninhados. | O relatório faz múltiplas consultas por curso e matrícula. |
| P2-04 | MEDIUM | `src/AppManager.js:50-61` grava matrícula, pagamento e auditoria em operações separadas sem transação nem tratamento do erro final. | Falhas intermediárias deixam dados inconsistentes ou retornam sucesso sem auditoria. |
| P2-05 | LOW | `src/AppManager.js:29-33` usa nomes locais `u`, `e`, `p`, `cid` e `cc`. | O fluxo de checkout se torna mais difícil de ler e revisar. |
| P2-06 | LOW | `src/AppManager.js:2` importa `totalRevenue`, mas não o utiliza. | O código sugere uma dependência inexistente e aumenta o ruído de manutenção. |

### Projeto 3 — `task-manager-api`

Stack: Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e SQLite. Domínio: usuários, tarefas, categorias e relatórios. Já existem pastas `models/`, `routes/`, `services/` e `utils/`, mas várias responsabilidades ainda estão nas rotas.

| ID | Severidade | Evidência | Impacto |
|---|---|---|---|
| P3-01 | CRITICAL | `models/user.py:20-32` expõe o hash da senha na serialização e usa MD5 sem algoritmo próprio para senhas. | Os hashes ficam acessíveis pela API e são inadequados para proteção de credenciais. |
| P3-02 | CRITICAL | `services/notification_service.py:7-10` contém usuário e senha SMTP no código. | A credencial é distribuída com o projeto e não pode ser gerenciada por ambiente. |
| P3-03 | MEDIUM | `routes/report_routes.py:53-56` busca tarefas separadamente para cada usuário. | O relatório de produtividade sofre com consultas N+1. |
| P3-04 | MEDIUM | `routes/user_routes.py:127-132` captura qualquer exceção sem identificar ou registrar a causa. | Erros de programação e falhas de banco recebem tratamento indistinto e difícil de diagnosticar. |
| P3-05 | LOW | `app.py:7` importa `os`, `sys` e `json` sem uso. | Imports supérfluos dificultam a leitura das dependências reais. |
| P3-06 | LOW | `utils/helpers.py:110-115` define constantes de validação, mas `utils/helpers.py:74-85` repete esses valores literalmente. | Regras simples podem divergir durante a manutenção. |

## Construção da Skill

A ferramenta escolhida foi o Codex. A skill `refactor-arch` está em `.agents/skills/refactor-arch/` dentro de cada subprojeto. O `SKILL.md` conduz análise, auditoria com pausa obrigatória e refatoração após confirmação explícita. Cinco arquivos Markdown em `references/` tratam das heurísticas de análise, do catálogo de 12 anti-patterns, do template de relatório, das responsabilidades MVC e do playbook com 14 transformações antes/depois. O catálogo usa a escala CRITICAL → LOW do enunciado; uma API só é declarada deprecated após conferir a versão aplicável.

A skill usa conceitos de linguagem, framework, banco e domínio na Fase 1 antes de escolher transformações. Assim, as mesmas instruções servem a Flask e Express. No Task Manager, que já possui camadas parciais, o playbook orienta melhorar os limites existentes. As três cópias foram validadas e comparadas por hash. A primeira execução real ocorreu no projeto 1, com invocação explícita de `$refactor-arch`; a sessão `01a0c6e5-7ffb-7831-b87d-2dec5f808a0b` parou após a auditoria e pediu confirmação. Após a confirmação do usuário, essa mesma sessão executou a Fase 3. O template foi reforçado e o catálogo ajustado à definição literal de CRITICAL durante a revisão; as três cópias foram sincronizadas.

## Resultados

### Projeto 1 — `code-smells-project`

O relatório pré-refatoração está em [`reports/audit-project-1.md`](reports/audit-project-1.md), com **15 findings: 6 CRITICAL, 2 HIGH, 4 MEDIUM e 3 LOW**. Ele identifica os seis problemas P1-01 a P1-06 da análise manual. Nenhuma API deprecated foi confirmada. As referências de arquivo e linha apontam para o código original do commit `6d1ce62`.

Antes, `app.py` registrava as rotas e incluía SQL administrativo; `controllers.py` misturava HTTP e regras de negócio; `models.py` misturava persistência e cálculo; `database.py` mantinha conexão global. Depois, `views.py` contém as rotas, `controllers.py` valida e coordena os fluxos, `models.py` concentra o acesso parametrizado aos dados, `database.py` gerencia a conexão por requisição, `config.py` lê o ambiente, `errors.py` define os erros esperados e `app.py` compõe a aplicação e centraliza o tratamento de erros.

O teste de integração usa SQLite em diretório temporário. `python -m unittest discover -s tests -v` passou com **6 testes**: inicialização, todos os endpoints públicos originais, casos de erro, bloqueio das rotas administrativas, migração de senha, transação de pedido, listagem em uma consulta e resposta sanitizada a falha de banco. O boot por `create_app()` e o primeiro acesso ao banco passaram. Exemplos de respostas verificadas: `GET /health` → 200 sem segredo ou caminho do banco; `POST /produtos` válido → 201; `POST /pedidos` válido → 201; login inválido → 401; pedido inexistente em atualização de status → 404; `POST /admin/query` e `/admin/reset-db` → 404.

Mudanças intencionais de contrato: as duas rotas administrativas foram removidas por permitirem SQL arbitrário e exclusão sem autorização; respostas de usuário e health não expõem credenciais; entradas inválidas são recusadas; atualização de pedido inexistente retorna 404. Usuários de exemplo com senhas conhecidas deixaram de ser criados. Bancos legados têm senhas convertidas para hash no primeiro acesso; faça backup antes de usar um banco existente. A extração de `config.py` foi acrescentada após a revisão independente da Fase 3.

#### Checklist do projeto 1

**Fase 1 — Análise**

- [x] Linguagem detectada corretamente: Python.
- [x] Framework detectado corretamente: Flask 3.1.1 declarado.
- [x] Domínio da aplicação descrito corretamente: loja com produtos, usuários, pedidos e vendas.
- [x] Número de arquivos analisados condiz com a realidade: quatro arquivos Python originais (`app.py`, `controllers.py`, `models.py`, `database.py`).

**Fase 2 — Auditoria**

- [x] Relatório segue o template definido nos arquivos de referência.
- [x] Cada finding tem arquivo e linhas exatos do código original.
- [x] Findings ordenados por severidade (CRITICAL → LOW).
- [x] Mínimo de 5 findings identificados: 15.
- [x] Detecção de APIs deprecated incluída: verificação feita; nenhuma confirmada.
- [x] Skill pausou e pediu confirmação antes da Fase 3; o usuário autorizou depois.

**Fase 3 — Refatoração**

- [x] Estrutura segue MVC: `models.py`, `views.py`, `controllers.py`.
- [x] Configuração extraída para `config.py` e variáveis de ambiente, sem credenciais hardcoded.
- [x] Models abstraem acesso aos dados.
- [x] Views/Routes separadas em `views.py`.
- [x] Controllers concentram o fluxo da aplicação.
- [x] Error handling centralizado em `app.py` com `APIError` em `errors.py`.
- [x] Entry point claro em `app.py`.
- [x] Aplicação inicia e inicializa o banco sem erros no teste isolado.
- [x] Endpoints originais respondem conforme testes; as mudanças de segurança estão documentadas acima.

### Projeto 2 — `ecommerce-api-legacy`

O relatório pré-refatoração está em [`reports/audit-project-2.md`](reports/audit-project-2.md), com **15 findings: 5 CRITICAL, 1 HIGH, 6 MEDIUM e 3 LOW**. Ele cobre os seis problemas P2-01 a P2-06 da análise manual e achados adicionais reproduzidos em baseline isolada. A revisão confirmou que o pacote `sqlite3` 5.1.7 está deprecated e sem manutenção, embora nenhuma assinatura deprecated do Express usada pelo código tenha sido encontrada. A sessão histórica `01a0c9df-2503-7823-8861-b945db324f5d` executou a análise antes da refatoração, mas seu diretório de trabalho era a raiz do repositório. Para verificar a descoberta real da skill, a sessão somente leitura `01a0cc78-5105-7963-b0bb-4f9078217fbc` foi iniciada em `ecommerce-api-legacy` no commit pré-refatoração `6060111`, invocou `$refactor-arch`, leu os seis arquivos da skill local, executou as Fases 1 e 2 e parou no confirmation gate sem alterar o checkout.

Antes, `AppManager.js` concentrava banco, rotas, checkout e relatório, enquanto `utils.js` guardava credenciais e criptografia frágil. Depois, `src/routes/apiRoutes.js` define a interface HTTP, `src/controllers/` coordena checkout e administração, `src/models/LmsRepository.js` concentra SQLite, `src/config.js` exige configuração externa, `src/constants.js` centraliza estados de pagamento, `src/security.js` usa `scrypt`, `src/errors.js` centraliza falhas e `src/app.js` compõe e inicia a aplicação.

`npm test` passou com **5 testes e 0 falhas**. A suíte inicia a aplicação em porta efêmera e SQLite em memória; cobre os quatro fluxos de `api.http`, os três endpoints originais em sucesso e erro, autorização administrativa, ausência de cartão e chave nos logs, hash de senha, relatório sem N+1, exclusão consistente e rollback quando a gravação do pagamento falha. Uma inicialização independente abriu o servidor e obteve 200 no relatório autenticado.

Mudanças intencionais de contrato: relatório e exclusão retornam 403 sem `X-Admin-Key`; usuário inexistente retorna 404; a exclusão remove matrículas e pagamentos relacionados; pagamento recusado não cria usuário parcial; `pwd` é obrigatório; erros inesperados retornam `Erro interno`. Os métodos e caminhos originais foram preservados. `ADMIN_API_KEY` e `PAYMENT_GATEWAY_KEY` são obrigatórios e estão documentados em `.env.example`, sem valores reais.

Risco restante documentado: a refatoração manteve o driver `sqlite3` para preservar escopo e compatibilidade. A migração para um driver mantido deve ser feita em mudança dedicada, com repetição dos testes de transação, integridade e relatório.

#### Checklist do projeto 2

**Fase 1 — Análise**

- [x] Linguagem detectada corretamente: JavaScript em Node.js 22.20.0.
- [x] Framework detectado corretamente: Express 4.22.1 instalado.
- [x] Domínio descrito corretamente: LMS com checkout, matrículas, pagamentos e relatório financeiro.
- [x] Número de arquivos analisados condiz com a realidade: três arquivos-fonte originais.

**Fase 2 — Auditoria**

- [x] Relatório segue o template definido nas referências.
- [x] Cada finding tem arquivo e linhas exatos do código original.
- [x] Findings ordenados por severidade (CRITICAL → LOW).
- [x] Mínimo de 5 findings identificado: 15.
- [x] Detecção de APIs deprecated incluída: pacote `sqlite3` deprecated; nenhuma assinatura deprecated do Express confirmada.
- [x] Skill pausou e pediu confirmação antes da Fase 3; o usuário autorizou depois.

**Fase 3 — Refatoração**

- [x] Estrutura de diretórios segue MVC para Express.
- [x] Configuração extraída para `src/config.js`, sem credenciais hardcoded.
- [x] Model/repository criado para abstrair SQLite.
- [x] Routes separadas em `src/routes/apiRoutes.js`.
- [x] Controllers concentram os fluxos da aplicação.
- [x] Error handling centralizado em `src/errors.js`.
- [x] Entry point claro em `src/app.js`.
- [x] Aplicação inicia sem erros em porta efêmera.
- [x] Todos os endpoints originais responderam nos testes; mudanças de segurança estão documentadas.

### Projeto 3 — `task-manager-api`

O relatório pré-refatoração está em [`reports/audit-project-3.md`](reports/audit-project-3.md), com **13 findings: 4 CRITICAL, 1 HIGH, 6 MEDIUM e 2 LOW**. Ele cobre P3-01 a P3-06 e confirmou duas famílias de API deprecated: `datetime.utcnow()` no Python 3.12 e `Query.get()` no SQLAlchemy 2. A sessão Codex `01a0cb5b-d36c-7213-ae37-98ba9efb8e02` executou `$refactor-arch`, analisou 15 arquivos Python e inventariou 22 regras de aplicação, depois parou até a confirmação explícita.

A organização parcial original foi preservada. Os Blueprints em `routes/` ficaram como adaptadores HTTP; novos módulos em `controllers/` concentram validação, consultas e transações; `models/` mantém entidades e serialização segura; `config.py` lê o ambiente; `errors.py` centraliza falhas; `utils/datetime_utils.py` padroniza UTC compatível com as colunas SQLite existentes. A configuração SMTP deixou o código e o seed passou a usar hash seguro.

A validação independente executou Python 3.12.13, Flask 3.0.0 e Flask-SQLAlchemy 3.1.1 via `uv`. `python -m unittest discover -s tests -v` passou com **6 testes e 0 falhas**. A suíte usa SQLite em memória, confirma exatamente 22 regras, exercita cada endpoint original em sucesso e erro, inicia um servidor HTTP real, verifica que nenhuma resposta expõe `password`, migra MD5 legado no login e limita queries nos antigos N+1.

Mudanças intencionais de contrato: hashes de senha não são mais retornados; filtros numéricos inválidos recebem 400; erros inesperados recebem JSON sanitizado; debug é externo e desabilitado por padrão; ausência de configuração SMTP impede tentativa de autenticação. Permanecem como riscos conhecidos o token de login fictício, ausência de autorização real, CORS irrestrito e relatórios sem paginação.

#### Checklist do projeto 3

**Fase 1 — Análise**

- [x] Linguagem detectada corretamente: Python 3.12.13 no runtime usado.
- [x] Framework detectado corretamente: Flask 3.0.0 e Flask-SQLAlchemy 3.1.1 declarados e executados.
- [x] Domínio descrito corretamente: usuários, tarefas, categorias e relatórios.
- [x] Número de arquivos analisados condiz com a realidade: 15 arquivos Python originais.

**Fase 2 — Auditoria**

- [x] Relatório segue o template definido nas referências.
- [x] Cada finding tem arquivo e linhas exatos do código original.
- [x] Findings ordenados por severidade (CRITICAL → LOW).
- [x] Mínimo de 5 findings identificado: 13.
- [x] Detecção de APIs deprecated incluiu `datetime.utcnow()` e `Query.get()`.
- [x] Skill pausou e pediu confirmação antes da Fase 3; o usuário autorizou depois.

**Fase 3 — Refatoração**

- [x] Estrutura parcial MVC foi preservada e completada com `controllers/`.
- [x] Configuração extraída para `config.py` e `.env.example`, sem credenciais hardcoded.
- [x] Models permanecem responsáveis pelas entidades e projeções públicas.
- [x] Views/Routes separadas em `routes/`, sem persistência direta.
- [x] Controllers concentram o fluxo da aplicação.
- [x] Error handling centralizado em `errors.py`.
- [x] Entry point e factory claros em `app.py`.
- [x] Aplicação inicia por HTTP sem erros em teste isolado.
- [x] Todos os 22 endpoints originais responderam em sucesso e erro representativo.

### Validação consolidada

Na revisão final, as três suítes passaram novamente em dados isolados: projeto 1 com 6 testes, projeto 2 com 5 testes e projeto 3 com 6 testes. As três cópias de `refactor-arch` passaram no `quick_validate.py`; os seis arquivos de cada cópia têm hashes idênticos. Os três relatórios estão em `reports/`, e os 57 itens dos checklists individuais estão marcados com evidência. O Git não rastreia bancos, ambientes, `node_modules`, caches Python nem arquivos `.env`. A busca por valores sensíveis encontrou apenas exemplos declarados no playbook e valores exclusivos de testes.

Evidência literal da última execução das suítes:

```text
code-smells-project
Ran 6 tests
OK

ecommerce-api-legacy
# tests 5
# pass 5
# fail 0

task-manager-api
Ran 6 tests
OK
```

Commits rastreáveis da implementação:

- `6060111` — skill, análise, auditoria e refatoração do projeto 1;
- `76db01f` — auditoria e refatoração do projeto 2;
- `6ac98d1` — auditoria e refatoração do projeto 3.

Os três projetos estão refatorados, documentados e validados. A entrega foi publicada em `origin/main` no fork público [AlexandreJareck/refactor-projects-skill](https://github.com/AlexandreJareck/refactor-projects-skill). A verificação anônima encontrou a `main` remota e obteve HTTP 200 no README publicado.

## Como Executar

Entre em cada subprojeto e invoque explicitamente `$refactor-arch` em uma sessão Codex. A skill deve apresentar as Fases 1 e 2 e aguardar confirmação específica antes da Fase 3. Para o projeto 1, instale `requirements.txt`, configure as variáveis opcionais de `.env.example`, execute `python app.py` e valide com `python -m unittest discover -s tests -v`. Use um banco SQLite separado para desenvolvimento e testes. No projeto 2, execute `npm ci`, defina `ADMIN_API_KEY` e `PAYMENT_GATEWAY_KEY`, rode `npm start` e valide com `npm test`; `api.http` mostra os corpos e o cabeçalho administrativo. No projeto 3, instale `requirements.txt`, configure `.env.example`, execute `python seed.py`, rode `python app.py` e valide com `python -m unittest discover -s tests -v`.
