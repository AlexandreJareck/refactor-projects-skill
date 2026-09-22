# Architecture audit - task-manager-api

## Project analysis
- Language and framework: Python 3.12.13 confirmado no runtime; Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e Flask-CORS 4.0.0 declarados em `requirements.txt`. A instalação dos pacotes não pôde ser introspectada porque o sandbox negou acesso ao cache preparado.
- Database and domain: SQLite com `users`, `tasks` e `categories`; domínio de usuários, tarefas, categorias e relatórios de produtividade.
- Architecture and entry point: separação parcial em Models, Blueprints, Services e Utils; `app.py` é o entry point/composition root, mas as rotas ainda acumulam regras, persistência e apresentação. O serviço de notificações não está conectado aos fluxos HTTP.
- Source files analyzed: 15 arquivos Python integralmente inspecionados; incluídos entry point, banco, seed e módulos internos, excluídos testes, dependências, gerados, documentação e skill.
- Original endpoints: `GET /`; `GET /health`; `GET|POST /users`; `GET|PUT|DELETE /users/<int:user_id>`; `GET /users/<int:user_id>/tasks`; `POST /login`; `GET|POST /tasks`; `GET|PUT|DELETE /tasks/<int:task_id>`; `GET /tasks/search`; `GET /tasks/stats`; `GET /reports/summary`; `GET /reports/user/<int:user_id>`; `GET|POST /categories`; `PUT|DELETE /categories/<int:cat_id>`.

## Summary
CRITICAL: 4 | HIGH: 1 | MEDIUM: 6 | LOW: 2 | Total: 13  
Deprecated APIs: TM-006, TM-008

Categorias do catálogo revisadas sem finding demonstrado: execução arbitrária de SQL/SQL injection, God Class com colapso completo, estado global mutável compartilhado por requisições e escrita multietapas parcialmente confirmada.

## Findings
### TM-001 [CRITICAL] Chave de assinatura Flask embutida no código
- File: `app.py:11-13`
- Evidence: a configuração contém uma `SECRET_KEY` literal e previsível, armazenada diretamente no repositório.
- Impact: qualquer mecanismo Flask que use essa chave para assinar cookies ou valores pode ser falsificado por quem tenha acesso ao código. O projeto atual não demonstra uso de sessão, mas a credencial já está exposta e não pode ser rotacionada por ambiente.
- Recommendation: obter a chave de variável de ambiente, exigir um valor forte no startup e manter apenas o nome da variável em um arquivo de exemplo.
- Manual-analysis match: additional finding

### TM-002 [CRITICAL] Hash de senha incluído na serialização pública
- File: `models/user.py:16-25`; response callers in `routes/user_routes.py:33-40`, `routes/user_routes.py:85-86`, `routes/user_routes.py:127-129`, `routes/user_routes.py:207-210`
- Evidence: `User.to_dict()` inclui o campo `password`; essa serialização é retornada por consulta individual, criação, atualização e login.
- Impact: clientes recebem hashes de senha, permitindo coleta e ataque offline; o risco é agravado pelo uso de MD5.
- Recommendation: criar uma projeção pública explícita que jamais contenha `password` e testar todas as respostas de usuário e login contra regressão.
- Manual-analysis match: P3-01

### TM-003 [CRITICAL] Senhas protegidas apenas com MD5
- File: `models/user.py:27-32`
- Evidence: `set_password()` e `check_password()` calculam diretamente `hashlib.md5()` sem salt adaptativo nem algoritmo específico para senhas.
- Impact: hashes capturados podem ser testados em alta velocidade; senhas curtas dos fixtures tornam a recuperação ainda mais barata.
- Recommendation: usar `werkzeug.security.generate_password_hash()` e `check_password_hash()`, atualizar seed e login em conjunto e definir uma estratégia de migração dos hashes existentes.
- Manual-analysis match: P3-01

### TM-004 [CRITICAL] Credencial SMTP armazenada no serviço
- File: `services/notification_service.py:7-10`
- Evidence: host, usuário e senha SMTP são literais no construtor. O valor da senha não é reproduzido neste relatório.
- Impact: a credencial é distribuída com o código e não pode ser rotacionada ou diferenciada por ambiente. Embora o serviço não esteja conectado às rotas atuais, qualquer uso da classe tentará autenticar com essa credencial exposta.
- Recommendation: carregar configuração SMTP do ambiente, validar campos obrigatórios no startup e substituir imediatamente qualquer credencial real que tenha usado esses valores.
- Manual-analysis match: P3-02

### TM-005 [HIGH] Blueprints concentram HTTP, regras e persistência
- File: `routes/report_routes.py:12-101`; `routes/task_routes.py:85-154`; `routes/task_routes.py:156-223`; `routes/user_routes.py:42-90`
- Evidence: as funções de rota leem requests, validam regras de domínio, consultam entidades, modificam Models, controlam commit/rollback, montam DTOs e escolhem respostas HTTP.
- Impact: regras não podem ser testadas sem contexto Flask e banco; criação e atualização já repetem validações e tratamentos distintos. Isso constitui forte violação de separação MVC, apesar da organização parcial existente.
- Recommendation: preservar os Blueprints e Models atuais, mas extrair somente os fluxos de usuário, tarefa, categoria e relatório para controllers/use cases. As rotas devem limitar-se a entrada HTTP, chamada do controller e serialização.
- Manual-analysis match: additional finding

### TM-006 [MEDIUM] `datetime.utcnow()` está deprecated no runtime instalado
- File: `models/category.py:11`; `models/task.py:15-16`; `models/task.py:52`; `models/user.py:14`; `routes/report_routes.py:35-45`; `routes/task_routes.py:31`; `seed.py:66-74`
- Evidence: o código usa repetidamente `datetime.utcnow`, inclusive como default de colunas. O runtime confirmado é Python 3.12.13; a documentação oficial marca `datetime.utcnow()` como deprecated desde Python 3.12 e recomenda um datetime UTC consciente de fuso. [Documentação oficial do Python](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow)
- Impact: o projeto depende de API programada para remoção e mistura timestamps UTC ingênuos, que podem ser interpretados como horário local em outras operações.
- Recommendation: padronizar `datetime.now(timezone.utc)` e decidir explicitamente como persistir/comparar timestamps conscientes no SQLite e SQLAlchemy antes da troca mecânica.
- Manual-analysis match: additional finding

### TM-007 [MEDIUM] Três endpoints executam consultas N+1
- File: `routes/report_routes.py:53-56`; `routes/report_routes.py:157-164`; `routes/task_routes.py:14-52`
- Evidence: o relatório consulta tarefas uma vez por usuário; a listagem de categorias conta tarefas uma vez por categoria; a listagem de tarefas busca usuário e categoria dentro do loop.
- Impact: o número de queries cresce com usuários, categorias e tarefas, degradando latência e carga do banco.
- Recommendation: usar agregação agrupada para produtividade e contagens, e eager loading ou joins para usuário/categoria na listagem de tarefas.
- Manual-analysis match: P3-03

### TM-008 [MEDIUM] `Query.get()` deprecated é usado em 16 pontos
- File: `routes/report_routes.py:105`; `routes/report_routes.py:192`; `routes/report_routes.py:213`; `routes/task_routes.py:42-67`; `routes/task_routes.py:117-122`; `routes/task_routes.py:158`; `routes/task_routes.py:188-195`; `routes/task_routes.py:227`; `routes/user_routes.py:29`; `routes/user_routes.py:94`; `routes/user_routes.py:136`; `routes/user_routes.py:155`
- Evidence: o projeto chama `Model.query.get()`. Flask-SQLAlchemy 3.1.1 exige SQLAlchemy 2.0.16 ou superior, conforme o changelog oficial; no SQLAlchemy 2.x, `Query.get()` é explicitamente deprecated e migrou para `Session.get()`. [Changelog oficial do Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/changes/), [documentação oficial do SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.get)
- Impact: o acesso depende da interface `Query` legada e acumula dívida de migração em quase todos os fluxos CRUD.
- Recommendation: substituir buscas por chave por `db.session.get(Model, id)`; para outras consultas, migrar gradualmente para `db.session.execute(db.select(...))`.
- Manual-analysis match: additional finding

### TM-009 [MEDIUM] Exceções amplas são silenciadas e mapeadas indistintamente
- File: `routes/report_routes.py:182-188`; `routes/task_routes.py:61-63`; `routes/task_routes.py:231-238`; `routes/user_routes.py:127-132`; `routes/user_routes.py:144-151`
- Evidence: diversos blocos usam `except:` ou capturam `Exception` sem logging estruturado, identificação do erro ou propagação para um handler central.
- Impact: erros de programação, falhas de banco e erros esperados tornam-se respostas 500 indistintas; exceções como `KeyboardInterrupt` também podem ser capturadas pelos `except:` nus.
- Recommendation: capturar apenas falhas esperadas junto ao limite apropriado e centralizar o mapeamento de exceções inesperadas para HTTP com logging sanitizado.
- Manual-analysis match: P3-04

### TM-010 [MEDIUM] Validações duplicadas e divergentes
- File: `routes/task_routes.py:85-138`; `routes/task_routes.py:156-205`; `routes/user_routes.py:42-72`; `routes/user_routes.py:92-121`; `utils/helpers.py:57-108`
- Evidence: criação e atualização repetem manualmente regras de título, status, prioridade, datas, email, senha e role; `process_task_data()` já contém outra implementação, mas não é utilizado.
- Impact: regras equivalentes retornam mensagens diferentes e podem evoluir de forma incompatível; por exemplo, criação e atualização de tarefa tratam datas e títulos separadamente.
- Recommendation: consolidar validação por domínio em funções ou schemas compartilhados, mantendo o mapeamento HTTP nas rotas.
- Manual-analysis match: P3-06

### TM-011 [MEDIUM] Filtros numéricos inválidos causam erro interno
- File: `routes/task_routes.py:240-271`
- Evidence: `priority` e `user_id` vêm diretamente de `request.args` e são convertidos com `int()` sem validação nem tratamento de `ValueError`.
- Impact: chamadas como `/tasks/search?priority=x` interrompem a rota e resultam em 500, em vez de um erro de entrada 400 estável.
- Recommendation: validar e converter filtros em uma camada comum de entrada, retornando erro de campo explícito antes de montar a query.
- Manual-analysis match: additional finding

### TM-012 [LOW] Imports não usados obscurecem dependências
- File: `app.py:7`; `models/task.py:3`; `routes/report_routes.py:1-8`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `utils/helpers.py:3-7`
- Evidence: `os`, `sys`, `json`, `time`, `hashlib`, `math`, `request`, `format_date` e `calculate_percentage`, entre outros, são importados sem uso nos respectivos módulos.
- Impact: aumenta o ruído e sugere dependências/responsabilidades que os módulos não possuem.
- Recommendation: remover apenas os imports confirmadamente não usados e habilitar uma verificação estática simples no fluxo de desenvolvimento.
- Manual-analysis match: P3-05

### TM-013 [LOW] Constantes de domínio existem, mas os mesmos valores permanecem literais
- File: `utils/helpers.py:74-85`; `utils/helpers.py:110-115`
- Evidence: `VALID_STATUSES`, limites de título, prioridade padrão e outros valores são definidos ao final do módulo, enquanto a própria validação e as rotas repetem listas e números literais.
- Impact: alterações podem atingir a constante sem mudar o comportamento efetivo, produzindo regras divergentes.
- Recommendation: manter uma única definição por regra e utilizá-la nos validadores compartilhados; não criar novas constantes para valores usados apenas uma vez.
- Manual-analysis match: P3-06

## Proposed MVC change
Preservar a estrutura parcial existente: `models/`, `routes/`, `services/` e `utils/`. Adicionar controllers/use cases por domínio apenas para retirar das rotas validação, orquestração e persistência. Manter os Models focados em dados, relacionamentos e consultas; usar o serviço de notificação por injeção somente onde houver um fluxo real. Extrair configuração para ambiente, criar um handler central de erros, substituir serializadores inseguros e corrigir as consultas N+1 e APIs deprecated. Não há justificativa para renomear ou reconstruir gratuitamente todas as pastas existentes.

## Confirmation gate
Phase 2 complete. Confirm Phase 3 before any file is written or changed.
