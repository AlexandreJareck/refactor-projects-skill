# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Configuração e validação após a refatoração

Use `.env.example` como referência. `TASK_MANAGER_DATABASE_URI` seleciona o banco, `TASK_MANAGER_SECRET_KEY` fornece o segredo da aplicação e `TASK_MANAGER_DEBUG` controla o debug. As variáveis `TASK_MANAGER_SMTP_*` configuram notificações; sem elas, o serviço não tenta autenticar nem enviar email. Nenhuma credencial possui valor literal no código.

A estrutura parcial original foi preservada. As rotas em `routes/` traduzem HTTP, os módulos em `controllers/` concentram validação e fluxo, `models/` mantém as entidades, `config.py` lê o ambiente e `errors.py` centraliza respostas de erro. Execute a validação com:

```bash
python -m unittest discover -s tests -v
```

Mudanças intencionais de contrato:

- Respostas de usuário, criação, atualização e login não incluem mais o hash de senha.
- Filtros numéricos inválidos de `/tasks/search` retornam 400, em vez de erro interno.
- Erros inesperados retornam `{"error":"Erro interno"}` sem detalhes sensíveis.
- Debug fica desabilitado por padrão e é controlado pelo ambiente.
- Hashes MD5 legados ainda são aceitos no primeiro login correto e são imediatamente substituídos por hash seguro.

Limitações conhecidas: o token de login permanece o valor fictício original; não há autorização real, CORS continua aberto e relatórios grandes ainda precisam de paginação ou agregação adicional.
