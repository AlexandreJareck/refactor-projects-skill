# Architecture audit - ecommerce-api-legacy

## Project analysis

- Language and framework: Node.js 22.20.0; Express `^4.18.2` declarado em `package.json` e 4.22.1 instalado.
- Database and domain: sqlite3 `^5.1.6` declarado e 5.1.7 instalado; SQLite `:memory:` com usuários, cursos, matrículas e pagamentos. O domínio é uma API de LMS com checkout e relatório financeiro.
- Architecture and entry point: `src/app.js` cria o Express, inicializa `AppManager` e abre a porta 3000. `src/AppManager.js` concentra banco, regras e rotas; `src/utils.js` contém configuração e utilitários.
- Source files analyzed: 3 — `src/app.js`, `src/AppManager.js` e `src/utils.js`, no estado anterior à refatoração do commit `6060111`.
- Original endpoints: `POST /api/checkout`; `GET /api/admin/financial-report`; `DELETE /api/users/:id`.
- Baseline isolada: uma instância nova do processo, Express em porta efêmera e SQLite em memória. Relatório inicial retornou 200; checkout incompleto, 400; curso ausente, 404; pagamento recusado, 400; checkout aprovado, 200. Exclusão de usuário inexistente e existente retornou 200; a exclusão existente deixou registros órfãos e o relatório passou a exibir `Unknown`. Um cartão numérico provocou `TypeError` não tratado e encerrou o servidor. A saída que continha cartão e chave foi suprimida.

## Summary

CRITICAL: **5** | HIGH: **1** | MEDIUM: **6** | LOW: **3** | Total: **15**

Deprecated APIs: **AUD-007** identifica o ciclo de vida deprecated e sem manutenção do pacote `sqlite3`, confirmado no [repositório oficial do node-sqlite3](https://github.com/TryGhost/node-sqlite3). Não foi encontrada uma assinatura deprecated do Express usada pelo código.

## Findings

### AUD-001 [CRITICAL] God Class reúne todas as responsabilidades

- File: `src/AppManager.js:4-139`
- Evidence: A mesma classe cria e popula tabelas, acessa o banco, executa checkout, monta relatório e registra rotas e respostas HTTP.
- Impact: O colapso de roteamento, persistência e regras complexas torna qualquer mudança ampla e arriscada.
- Recommendation: Separar rotas, controladores de fluxo, serviços e persistência; manter a composição no ponto de entrada.
- Manual-analysis match: P2-02

### AUD-002 [CRITICAL] Senha fraca e credencial de seed em texto claro

- File: `src/AppManager.js:18,68-69`; `src/utils.js:17-22`
- Evidence: O seed grava `123`, e `badCrypto` apenas repete Base64 e trunca o resultado a dez caracteres.
- Impact: Senhas podem ser recuperadas ou colidir e uma credencial utilizável é distribuída no código.
- Recommendation: Usar hash específico para senhas com salt e parâmetros apropriados; remover senha conhecida do seed.
- Manual-analysis match: additional finding

### AUD-003 [CRITICAL] Cartão completo e chave de pagamento no log

- File: `src/AppManager.js:45`
- Evidence: O `console.log` interpola o cartão integral e `config.paymentGatewayKey`; a baseline acionou esse caminho e suprimiu o conteúdo.
- Impact: Dados de pagamento e credenciais podem ficar expostos a operadores e coletores de logs.
- Recommendation: Remover cartão e chave dos logs e registrar apenas eventos e identificadores seguros.
- Manual-analysis match: P2-01

### AUD-004 [CRITICAL] Operações administrativas e destrutivas sem autorização

- File: `src/AppManager.js:80-129,131-137`
- Evidence: Relatório financeiro e exclusão de usuário são registrados sem autenticação ou autorização.
- Impact: Qualquer cliente alcançável pode consultar informações financeiras ou apagar usuários.
- Recommendation: Exigir autorização administrativa antes dos handlers e testar acessos permitido e negado.
- Manual-analysis match: additional finding

### AUD-005 [CRITICAL] Credenciais embutidas na configuração

- File: `src/utils.js:1-6`
- Evidence: Usuário, senha do banco e chave do gateway são literais no código.
- Impact: Segredos são distribuídos com a aplicação e não podem ser rotacionados por ambiente com segurança.
- Recommendation: Carregar segredos de ambiente ou gerenciador de segredos e falhar claramente quando ausentes.
- Manual-analysis match: additional finding

### AUD-006 [HIGH] Cache global mutável compartilhado

- File: `src/utils.js:9-15`
- Evidence: `globalCache` é um objeto mutável no escopo do módulo, acessível por todas as requisições e instâncias.
- Impact: Estado pode vazar entre requisições e testes, produzir concorrência incorreta e crescer sem política de expiração.
- Recommendation: Remover o estado global ou encapsular cache com ciclo de vida, limites e invalidação explícitos.
- Manual-analysis match: additional finding

### AUD-007 [MEDIUM] Driver SQLite deprecated e sem manutenção

- File: `package.json:11`; `src/AppManager.js:1`
- Evidence: A aplicação depende diretamente de `sqlite3`; o repositório oficial do pacote o declara deprecated/unmaintained.
- Impact: Correções futuras de compatibilidade e segurança deixam de ser garantidas pelo mantenedor.
- Recommendation: Planejar migração para um driver SQLite mantido, com testes de compatibilidade e transação antes da troca.
- Manual-analysis match: additional finding

### AUD-012 [MEDIUM] Exclusão deixa órfãos e confirma ausência como sucesso

- File: `src/AppManager.js:12-16,131-136`
- Evidence: Não há chaves estrangeiras com cascata; o handler exclui só `users`, ignora erro e `changes`. A baseline confirmou 200 para ID inexistente e registros órfãos para ID existente.
- Impact: A API relata sucesso incorreto e o relatório perde a identidade do aluno.
- Recommendation: Aplicar integridade referencial e transação, tratar erro e devolver 404 quando nenhuma linha for alterada.
- Manual-analysis match: additional finding

### AUD-008 [MEDIUM] Tipo inesperado de cartão derruba o processo

- File: `src/AppManager.js:29-35,45-46`
- Evidence: A validação aceita qualquer valor truthy; depois chama `startsWith` diretamente. Na baseline, cartão numérico produziu `TypeError` não tratado e encerrou o servidor.
- Impact: Uma entrada HTTP malformada pode causar indisponibilidade do processo.
- Recommendation: Validar tipos e formato antes do uso e encaminhar falhas ao tratamento central de erros.
- Manual-analysis match: additional finding

### AUD-009 [MEDIUM] Checkout grava registros relacionados sem transação

- File: `src/AppManager.js:50-61,68-71`
- Evidence: Usuário, matrícula, pagamento e auditoria são gravados em callbacks separados, sem `BEGIN`, `COMMIT` e `ROLLBACK`.
- Impact: Falhas intermediárias deixam dados parciais e inconsistentes.
- Recommendation: Executar todo o checkout em transação e confirmar a resposta somente após o commit.
- Manual-analysis match: P2-04

### AUD-010 [MEDIUM] Relatório executa consultas N+1

- File: `src/AppManager.js:89-106`
- Evidence: Para cada curso busca matrículas e, para cada matrícula, consulta usuário e pagamento separadamente.
- Impact: O número de consultas cresce com cursos e alunos, aumentando a latência.
- Recommendation: Usar `JOIN` e agregação ou consultas em lote, preservando a estrutura da resposta.
- Manual-analysis match: P2-03

### AUD-011 [MEDIUM] Erros assíncronos são ignorados

- File: `src/AppManager.js:92-106`
- Evidence: Callbacks do relatório não verificam `err`, e o fluxo usa resultados como se as consultas sempre tivessem êxito.
- Impact: Falhas de banco podem gerar exceção, resposta parcial ou requisição sem término previsível.
- Recommendation: Propagar todos os erros ao middleware central e responder apenas após concluir todas as operações.
- Manual-analysis match: additional finding

### AUD-013 [LOW] Utilitário e importação sem uso

- File: `src/AppManager.js:2`; `src/utils.js:10,25`
- Evidence: `totalRevenue` é importado, mas não usado; o `globalCache` também não participa de um fluxo funcional conhecido.
- Impact: O código sugere dependências e comportamentos inexistentes e aumenta o ruído de manutenção.
- Recommendation: Remover código morto e manter apenas utilitários com consumidor identificado.
- Manual-analysis match: P2-06

### AUD-014 [LOW] Estados e senha padrão como valores mágicos

- File: `src/AppManager.js:21,46-48,68,108`
- Evidence: `PAID`, `DENIED` e a senha padrão são repetidos como literais no fluxo e no seed.
- Impact: Regras de domínio ficam dispersas e sujeitas a divergência.
- Recommendation: Centralizar estados de pagamento e retirar a senha padrão conhecida.
- Manual-analysis match: additional finding

### AUD-015 [LOW] Nomes locais pouco descritivos no checkout

- File: `src/AppManager.js:29-33`
- Evidence: Entradas são atribuídas a `u`, `e`, `p`, `cid` e `cc`.
- Impact: O fluxo de pagamento fica mais difícil de revisar e manter.
- Recommendation: Usar nomes que expressem usuário, email, senha, curso e cartão.
- Manual-analysis match: P2-05

## Proposed MVC change

Separar rotas Express, coordenação de checkout e administração e acesso SQLite em módulos de rota, controlador e modelo/repository. Centralizar tratamento de erros, configuração e constantes; adicionar autorização às rotas sensíveis e transação ao checkout. Preservar os contratos dos três endpoints quando compatíveis com as correções e documentar mudanças intencionais. Planejar separadamente a migração do driver SQLite deprecated.

## Confirmation gate

Phase 2 complete. **Confirm Phase 3 before any file is written or changed.**
