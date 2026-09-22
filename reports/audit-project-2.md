# Architecture audit - ecommerce-api-legacy

## Project analysis

- Language and framework: Node.js 22.20.0; Express `^4.18.2` declarado em `package.json` e **4.22.1 instalado**, confirmado por `npm ls`.
- Database and domain: sqlite3 `^5.1.6` declarado e **5.1.7 instalado**; SQLite `:memory:` com seeds de usuários, cursos, matrículas e pagamentos. O domínio é uma API de LMS com checkout e relatório financeiro.
- Architecture and entry point: `src/app.js` cria o Express, inicializa `AppManager` e abre a porta 3000. `src/AppManager.js` concentra banco, regras de negócio e rotas; `src/utils.js` contém configuração e utilitários.
- Source files analyzed: **3** arquivos de código fonte inspecionados integralmente (`src/app.js`, `src/AppManager.js`, `src/utils.js`). A contagem exclui dependências, arquivos gerados, testes, documentação e arquivos da skill.
- Original endpoints: `POST /api/checkout`; `GET /api/admin/financial-report`; `DELETE /api/users/:id`.
- Reproduzibilidade da linha de base: em um processo Node novo, instanciei `AppManager`, executei `initDb()` e `setupRoutes(app)` em uma instância Express, e usei uma porta efêmera em `127.0.0.1`. Cada execução começa com SQLite isolado em memória. Executei, na ordem, os quatro pedidos de `api.http`; suprimi a saída do log que contém cartão e chave.

| Pedido, na ordem de `api.http` | Status | Resposta | Contagens após o pedido: usuários / matrículas / pagamentos / auditorias |
|---|---:|---|---|
| Seed, antes dos pedidos | — | — | 1 / 1 / 1 / 0 |
| Checkout aprovado, curso 2 | 200 | `{"msg":"Sucesso","enrollment_id":2}` | 2 / 2 / 2 / 1 |
| Pagamento recusado, curso 1 | 400 | `Pagamento recusado` | 3 / 2 / 2 / 1 |
| Relatório financeiro | 200 | Clean Architecture: receita 997, Leonan; Docker: receita 497, Guilherme | 3 / 2 / 2 / 1 |
| Exclusão de `/api/users/1` | 200 | Mensagem informando que matrículas e pagamentos permaneceram | 2 / 2 / 2 / 1 |

No mesmo banco isolado, checkout com apenas `usr` retornou **400** (`Bad Request`); curso `999` com os demais campos presentes retornou **404** (`Curso não encontrado`); `DELETE /api/users/999` retornou **200**, mesmo sem usuário excluído. Após excluir o usuário 1, o relatório ainda mostrou receita 997 e o aluno `Unknown`.

Também injetei, somente em outra instância SQLite em memória, um gatilho que rejeita a inserção do novo pagamento. O checkout retornou **500** (`Erro Pagamento`), mas deixou **1 usuário e 1 matrícula novos, sem pagamento novo**. Isso confirma o efeito da ausência de transação.

## Summary

CRITICAL: **5** | HIGH: **0** | MEDIUM: **3** | LOW: **2** | Total: **10**

Deprecated APIs: **none verified**. Para as versões instaladas, conferi as chamadas usadas na [referência oficial do Express 4](https://expressjs.com/en/4x/api/), na [API oficial do node-sqlite3](https://github.com/TryGhost/node-sqlite3/wiki/API) e na [documentação oficial de `serialize`](https://github.com/TryGhost/node-sqlite3/wiki/Control-Flow). Não há uso demonstrado de assinatura de API marcada como deprecated nessas chamadas. Avisos sobre dependências transitivas no lockfile não foram tratados como APIs usadas pelo código.

## Findings

### A-01 [CRITICAL] God Class reúne todas as responsabilidades

- File: `src/AppManager.js:4-139`
- Evidence: A mesma classe cria e popula tabelas, acessa o banco, executa o checkout, monta o relatório e registra as três rotas e respostas HTTP.
- Impact: Viola completamente a separação de responsabilidades do exemplo de *God Class* no enunciado; mudanças em qualquer fluxo exigem alterar e testar a mesma classe.
- Recommendation: Separar rotas, controladores de fluxo e modelos de persistência por domínio; manter a composição no ponto de entrada.
- Manual-analysis match: P2-02

### A-02 [CRITICAL] Cartão completo e chave de pagamento no log

- File: `src/AppManager.js:45`
- Evidence: O `console.log` interpola o número integral recebido em `card` e `config.paymentGatewayKey`. A execução da linha de base acionou esse log; seu conteúdo foi suprimido na coleta.
- Impact: Dados de pagamento e material de credencial podem ser expostos a quem acessa logs.
- Recommendation: Remover cartão e chave dos logs; registrar apenas identificadores seguros e eventos necessários.
- Manual-analysis match: P2-01

### A-03 [CRITICAL] Relatório administrativo e exclusão sem autorização

- File: `src/AppManager.js:80,131-135`
- Evidence: As rotas de relatório administrativo e exclusão de usuário são registradas sem middleware ou verificação de identidade ou permissão. Chamadas sem credenciais receberam 200 na linha de base.
- Impact: Qualquer cliente com acesso à API pode consultar o relatório e solicitar exclusões.
- Recommendation: Exigir autenticação e autorização administrativa antes desses handlers e testar acesso permitido e negado.
- Manual-analysis match: additional finding

### A-04 [CRITICAL] Credenciais embutidas na configuração

- File: `src/utils.js:2-4`
- Evidence: O código contém valores literais para usuário e senha de banco e chave de gateway; a chave também é referenciada no checkout. A validade externa desses valores não foi verificada.
- Impact: Valores de credencial são distribuídos com o código e difíceis de substituir ou revogar por ambiente.
- Recommendation: Ler segredos de variáveis de ambiente ou de um gerenciador de segredos e retirar os valores do código e dos logs.
- Manual-analysis match: additional finding

### A-05 [CRITICAL] Hash de senha reversível e truncado

- File: `src/utils.js:17-22`
- Evidence: `badCrypto` repete Base64 da senha e retorna apenas dez caracteres; `src/AppManager.js:68-69` usa o resultado como senha armazenada.
- Impact: O valor não oferece proteção adequada para senhas e pode gerar colisões.
- Recommendation: Usar uma biblioteca de hash específica para senhas, com salt e parâmetros apropriados, e planejar a migração dos registros existentes.
- Manual-analysis match: additional finding

### A-06 [MEDIUM] Checkout grava registros relacionados sem transação

- File: `src/AppManager.js:50-61`
- Evidence: Matrícula, pagamento e auditoria são inseridos separadamente; o erro da auditoria é ignorado. Com falha injetada no pagamento em banco isolado, a resposta foi 500 e a matrícula permaneceu.
- Impact: Falhas intermediárias deixam registros parciais; a auditoria pode falhar mesmo quando a resposta informa sucesso.
- Recommendation: Executar as gravações relacionadas em transação, fazer rollback em qualquer erro e responder somente após sua confirmação.
- Manual-analysis match: P2-04

### A-07 [MEDIUM] Relatório executa consultas N+1

- File: `src/AppManager.js:89-106`
- Evidence: Para cada curso há uma consulta de matrículas e, para cada matrícula, consultas adicionais de usuário e pagamento. Com dois cursos e duas matrículas, o fluxo faz sete consultas de leitura.
- Impact: A quantidade de consultas cresce com os cursos e alunos, elevando a latência do relatório.
- Recommendation: Buscar os dados com `JOIN` e agregação ou com consultas em lote, mantendo a estrutura da resposta.
- Manual-analysis match: P2-03

### A-08 [MEDIUM] Exclusão deixa registros órfãos e confirma ausência como sucesso

- File: `src/AppManager.js:131-135`
- Evidence: O handler exclui apenas `users`, ignora `err` e não verifica `changes`. Após excluir o usuário 1, matrícula e pagamento permaneceram; excluir o usuário 999 também retornou 200.
- Impact: O relatório passa a mostrar `Unknown` para uma matrícula existente, e o cliente não consegue distinguir exclusão efetiva de usuário inexistente ou falha de banco.
- Recommendation: Definir a política de retenção de matrículas e pagamentos, aplicar integridade referencial ou uma operação transacional compatível, tratar erro e verificar linhas afetadas.
- Manual-analysis match: additional finding

### A-09 [LOW] Importação sem uso

- File: `src/AppManager.js:2`
- Evidence: `totalRevenue` é importado, mas não é referenciado na classe.
- Impact: Sugere uma dependência inexistente e acrescenta ruído à leitura.
- Recommendation: Remover a importação não usada.
- Manual-analysis match: P2-06

### A-10 [LOW] Nomes locais pouco descritivos no checkout

- File: `src/AppManager.js:29-33`
- Evidence: Os valores de entrada são atribuídos a `u`, `e`, `p`, `cid` e `cc`.
- Impact: Dificulta acompanhar e revisar o fluxo de pagamento.
- Recommendation: Usar nomes que indiquem usuário, email, senha, identificador do curso e cartão.
- Manual-analysis match: P2-05

## Proposed MVC change

Separar o registro das rotas Express, a coordenação do checkout e do relatório, e o acesso SQLite em módulos de rota, controlador e modelo. Centralizar tratamento de erros e configuração; adicionar autorização às rotas sensíveis e transação ao checkout. Preservar os contratos dos três endpoints quando compatíveis com as correções de segurança e documentar qualquer mudança intencional.

## Confirmation gate

Phase 2 complete. Confirm Phase 3 before any file is written or changed.
