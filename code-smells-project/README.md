# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, com produtos de exemplo.

## Configuração e contratos após a refatoração

Configure `LOJA_DATABASE` para escolher o banco SQLite, `LOJA_HOST` e `LOJA_PORT` para o servidor e `LOJA_DEBUG=1` somente em desenvolvimento. `LOJA_SECRET_KEY` é opcional enquanto a API não usa sessões. Consulte `.env.example`; não armazene segredos no repositório.

O primeiro boot ainda cria produtos de exemplo, mas **não cria usuários com senhas conhecidas**. Crie um usuário por `POST /usuarios` antes de fazer login ou criar pedidos. Senhas de bancos antigos são convertidas para hashes no primeiro acesso após a atualização; mantenha uma cópia de segurança antes de migrar um banco existente.

Os métodos e caminhos públicos de produtos, usuários, login, pedidos, relatórios, `/health` e `/` continuam. Alterações intencionais de contrato:

- `POST /admin/query` e `POST /admin/reset-db` deixam de existir e retornam 404. Eram operações de leitura/alteração arbitrária e exclusão sem autorização.
- `GET /usuarios` e `GET /usuarios/<id>` deixam de incluir `senha`. `/health` deixa de incluir chave secreta, caminho do banco, modo de depuração e ambiente.
- Produto, usuário e item de pedido inválidos recebem erros 400; categoria e comprimento de nome também são validados na atualização. Um pedido com quantidade zero ou negativa é recusado.
- `PUT /pedidos/<id>/status` retorna 404 se o pedido não existe, em vez de informar sucesso.
- Erros inesperados retornam `{"erro":"Erro interno"}` sem detalhes internos.

Para executar os testes de integração com banco temporário: `python -m unittest discover -s tests -v`.
