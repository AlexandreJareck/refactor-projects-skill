# Architecture audit - code-smells-project

## Project analysis

- Language and framework: Python; Flask 3.1.1 e Flask-CORS 5.0.1 declarados em `requirements.txt`. As versões instaladas não puderam ser verificadas neste ambiente.
- Database and domain: SQLite; API de loja com produtos, usuários, pedidos e relatório de vendas. `database.py` cria as tabelas `produtos`, `usuarios`, `pedidos` e `itens_pedido` e insere dados de exemplo.
- Architecture and entry point: `app.py` registra as rotas e inicia o servidor; `controllers.py` recebe requisições; `models.py` combina consultas com parte das regras de negócio; `database.py` fornece uma conexão global. Há módulos separados, portanto o sinal de **God Class com colapso completo de responsabilidades** do catálogo não se confirma neste projeto.
- Source files analyzed: 4 — `app.py`, `controllers.py`, `models.py` e `database.py`. Contagem dos arquivos-fonte Python efetivamente inspecionados, excluindo dependências, arquivos gerados, testes e arquivos da skill. As linhas referem-se ao código original do commit `6d1ce62`; esses quatro arquivos não apresentam diferenças no Git.
- Original endpoints: GET `/`, `/health`, `/produtos`, `/produtos/busca`, `/produtos/<int:id>`, `/usuarios`, `/usuarios/<int:id>`, `/pedidos`, `/pedidos/usuario/<int:usuario_id>`, `/relatorios/vendas`; POST `/produtos`, `/usuarios`, `/login`, `/pedidos`, `/admin/reset-db`, `/admin/query`; PUT `/produtos/<int:id>`, `/pedidos/<int:pedido_id>/status`; DELETE `/produtos/<int:id>`. O inventário foi conferido no código. Não houve linha de base HTTP em execução porque não há interpretador Python acessível neste ambiente.

## Summary

CRITICAL: 6 | HIGH: 2 | MEDIUM: 4 | LOW: 3 | Total: 15

Deprecated APIs: none verified. A checagem considerou as versões declaradas e a [documentação do Flask 3.1](https://flask.palletsprojects.com/en/stable/api/) e do [Flask-CORS 5.0.1](https://github.com/corydolphin/flask-cors/tree/5.0.1); as versões instaladas não puderam ser consultadas.

Os seis IDs P1-01 a P1-06 da seção **Análise Manual** do README da raiz continuam confirmados. **P1-02 agora está classificado como CRITICAL no README**, em acordo com A04 e A05 e com o catálogo corrigido. A chave fixa e exposta de A03 também é CRITICAL. Não foi incluído um achado de God Class completa, pois nenhum componente reúne sozinho roteamento, persistência, fluxos complexos e apresentação HTTP de múltiplos domínios.

## Findings

### A03 [CRITICAL] Chave secreta fixa e exposta

- File: `app.py:7-9`; `controllers.py:285-290`; `app.py:88`
- Evidence: A aplicação define uma chave secreta literal, devolve seu valor em `/health` e inicia o servidor com depuração habilitada.
- Impact: Clientes podem obter a credencial da aplicação e informações internas de configuração.
- Recommendation: Carregar o segredo de configuração externa, retirar campos sensíveis da resposta e limitar a depuração ao desenvolvimento.
- Manual-analysis match: additional finding

### A02 [CRITICAL] Reinicialização pública do banco

- File: `app.py:47-55`
- Evidence: POST `/admin/reset-db` apaga registros das quatro tabelas e confirma a operação sem verificar autorização.
- Impact: Um cliente que alcance a rota pode apagar os dados da loja.
- Recommendation: Retirar a operação da API exposta ou restringi-la a uma função administrativa autenticada e isolada.
- Manual-analysis match: additional finding

### A01 [CRITICAL] Execução arbitrária de SQL

- File: `app.py:59-75`
- Evidence: POST `/admin/query` entrega o campo `sql` recebido por HTTP diretamente a `cursor.execute` e confirma comandos de alteração, sem verificar autorização.
- Impact: Um cliente pode consultar ou modificar o banco por meio de SQL escolhido por ele.
- Recommendation: Remover o endpoint de SQL arbitrário e oferecer somente operações administrativas específicas e protegidas, se necessárias.
- Manual-analysis match: P1-01

### A05 [CRITICAL] Senhas devolvidas pela API

- File: `models.py:72-86`; `models.py:89-102`
- Evidence: As funções de listagem e busca de usuários incluem `senha` nos objetos devolvidos aos controladores.
- Impact: As respostas de `/usuarios` e `/usuarios/<int:id>` expõem as senhas armazenadas.
- Recommendation: Usar uma representação pública de usuário que sempre exclua o campo de senha.
- Manual-analysis match: P1-02

### A06 [CRITICAL] SQL montado com entradas do cliente

- File: `models.py:47-49`; `models.py:57-61`; `models.py:109-111`; `models.py:126-129`; `models.py:289-299`
- Evidence: Login, busca e gravações concatenam valores recebidos do cliente ao texto SQL antes de executá-lo.
- Impact: Entradas com sintaxe SQL podem alterar consultas ou causar erros; login e busca possuem caminhos diretos de entrada HTTP.
- Recommendation: Parametrizar todos os valores e montar em código apenas a estrutura permitida das consultas.
- Manual-analysis match: additional finding

### A04 [CRITICAL] Senhas armazenadas sem hash próprio para senhas

- File: `database.py:75-82`; `models.py:109-110`; `models.py:122-130`
- Evidence: `criar_usuario` grava a senha recebida diretamente; o login a compara diretamente na consulta; os usuários de exemplo também são inseridos com senhas literais.
- Impact: O acesso aos registros do banco revela senhas utilizáveis.
- Recommendation: Aplicar uma função de hash específica para senhas com sal, migrar registros existentes e adaptar login e dados de exemplo.
- Manual-analysis match: P1-02

### A07 [HIGH] Conexão SQLite global compartilhada

- File: `database.py:4-11`
- Evidence: `get_db()` reutiliza uma conexão global com `check_same_thread=False`, sem ciclo de vida por requisição.
- Impact: Requisições concorrentes podem interferir nas operações e transações da mesma conexão.
- Recommendation: Gerir uma conexão por contexto de requisição, fechá-la ao final e definir o limite transacional de cada operação.
- Manual-analysis match: additional finding

### A08 [HIGH] Regras de negócio no módulo de modelos

- File: `models.py:133-169`; `models.py:235-273`
- Evidence: `criar_pedido` valida estoque, calcula total e coordena gravações; `relatorio_vendas` calcula faixas de desconto e indicadores junto das consultas SQL.
- Impact: Regras de pedido e relatório ficam acopladas à persistência, dificultando mudanças e testes isolados.
- Recommendation: Colocar a orquestração e os cálculos de domínio na camada de controle ou serviço e manter funções de acesso a dados com responsabilidades delimitadas.
- Manual-analysis match: additional finding

### A10 [MEDIUM] Validação de produto duplicada e divergente

- File: `controllers.py:24-54`; `controllers.py:64-92`
- Evidence: Criação e atualização repetem verificações de campos, preço e estoque; a atualização omite os limites de nome e a validação de categoria presentes na criação.
- Impact: Dados aceitos na atualização podem violar regras exigidas na criação.
- Recommendation: Centralizar a validação de produto e aplicar as mesmas regras às operações que compartilham o contrato.
- Manual-analysis match: P1-04

### A11 [MEDIUM] Quantidade de pedido sem validação de domínio

- File: `controllers.py:195-203`; `models.py:139-146`; `models.py:163-165`
- Evidence: O controlador exige uma lista não vazia, mas não exige quantidade positiva. Uma quantidade negativa passa pela comparação de estoque, reduz o total e é subtraída do estoque.
- Impact: Um pedido pode produzir valor negativo e aumentar indevidamente o estoque.
- Recommendation: Validar cada item e exigir IDs e quantidades inteiros válidos, com quantidade maior que zero, antes das gravações.
- Manual-analysis match: additional finding

### A09 [MEDIUM] Consultas N+1 na listagem de pedidos

- File: `models.py:174-192`; `models.py:206-224`
- Evidence: As duas funções de listagem consultam itens dentro do loop de pedidos e produtos dentro do loop de itens.
- Impact: O número de consultas cresce com a quantidade de pedidos e itens.
- Recommendation: Buscar itens e produtos por junção ou em lotes e agrupar os resultados.
- Manual-analysis match: P1-03

### A12 [MEDIUM] Atualização de status aceita pedido inexistente

- File: `controllers.py:237-252`; `models.py:275-283`
- Evidence: O modelo não verifica quantas linhas o `UPDATE` alterou; para um status válido, o controlador devolve sucesso sem confirmar que o pedido existe.
- Impact: A API informa que uma alteração ocorreu mesmo quando não há pedido correspondente.
- Recommendation: Verificar o resultado da atualização e devolver resposta de não encontrado quando nenhuma linha for alterada.
- Manual-analysis match: additional finding

### A13 [LOW] Diagnósticos com `print` nas rotas

- File: `controllers.py:5-12`
- Evidence: A rota imprime a contagem de produtos e o erro diretamente; outras rotas também usam `print` para registrar eventos.
- Impact: Os registros não têm nível nem contexto estruturado, dificultando a investigação de falhas.
- Recommendation: Usar logging com níveis e contexto adequados.
- Manual-analysis match: P1-05

### A14 [LOW] Categorias válidas embutidas no endpoint

- File: `controllers.py:52-54`
- Evidence: A lista de categorias é definida literalmente na criação de produto e não é reutilizada pela atualização.
- Impact: A manutenção das opções de domínio depende de sincronizar regras em lugares diferentes.
- Recommendation: Definir um conjunto compartilhado de categorias e reutilizá-lo na validação de produto.
- Manual-analysis match: P1-06

### A15 [LOW] Importações não usadas

- File: `database.py:2`; `models.py:2`
- Evidence: `os` e `sqlite3`, respectivamente, são importados sem uso nesses módulos.
- Impact: As importações acrescentam ruído à leitura do código.
- Recommendation: Remover as importações não usadas.
- Manual-analysis match: additional finding

## Proposed MVC change

Manter as rotas e separar por domínio a validação, os fluxos de negócio e o acesso a dados. Parametrizar consultas, gerir a conexão SQLite por requisição e retirar credenciais e operações administrativas inseguras da superfície pública. Preservar os contratos HTTP compatíveis com as correções e identificar mudanças necessárias para eliminar exposições comprovadas. Esta proposta não foi executada.

## Confirmation gate

Fase 2 concluída. **Você confirma explicitamente o início da Fase 3 antes que qualquer arquivo seja escrito ou alterado?**
