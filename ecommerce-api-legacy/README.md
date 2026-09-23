# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
$env:ADMIN_API_KEY = "development-admin-key"
$env:PAYMENT_GATEWAY_KEY = "development-gateway-key"
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

As rotas administrativas exigem o cabeçalho `X-Admin-Key` com o valor de
`ADMIN_API_KEY`. Configure também `PAYMENT_GATEWAY_KEY`; nenhum segredo possui
valor padrão no código. Em shells POSIX, use `export NOME=valor` em vez de
`$env:NOME = "valor"`.

## Mudanças intencionais de contrato

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` agora retornam
  `403 Acesso negado` sem um `X-Admin-Key` válido.
- Uma exclusão válida ainda retorna 200, agora com `Usuário deletado`; usuário
  inexistente retorna `404 Usuário não encontrado`. Matrículas e pagamentos do
  usuário são removidos pela integridade referencial.
- Checkout recusado continua retornando `400 Pagamento recusado`, sem criar um
  usuário parcial. Todos os campos de `api.http`, incluindo `pwd`, são exigidos.
- Erros inesperados retornam `500 Erro interno`; detalhes ficam somente no log
  sanitizado.

O código está separado em rotas Express, controladores de caso de uso e um
repositório SQLite. A inicialização e a composição das dependências ficam em
`src/app.js`, os estados de pagamento ficam em `src/constants.js` e os erros
HTTP são convertidos em um único middleware.

## Risco conhecido

O driver `sqlite3` foi mantido para preservar o escopo desta refatoração, mas o
pacote está deprecated e sem manutenção. A migração para um driver mantido deve
ser feita separadamente, repetindo os testes de transação, integridade e relatório.
