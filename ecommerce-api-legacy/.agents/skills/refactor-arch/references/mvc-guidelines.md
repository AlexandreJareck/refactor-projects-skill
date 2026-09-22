# MVC target for backend APIs

- **Model / data access:** owns persistence, queries, entities and data mapping. Never imports the HTTP framework to build responses. Keep SQL parameterized and transactions explicit.
- **View / route:** declares method and path, parses HTTP input, calls a controller and serializes its result. In JSON APIs, a route and response presenter fulfill the view role; HTML templates are not required.
- **Controller:** orchestrates a use case, coordinates models/services, applies domain rules and produces a result or typed error. Avoid direct framework-specific response creation when it would prevent testing.
- **Config:** loads environment-specific values and fails clearly when required secrets are missing. Ship an example environment file without real secrets.
- **Error handling:** centralize exception-to-HTTP mapping and sanitized logging. Distinguish expected validation/not-found errors from unexpected failures.
- **Entry point:** composes dependencies, registers routes and starts the server only when executed; make test construction possible.

Flask may use Blueprints plus controllers and repositories/SQLAlchemy models. Express may use Router modules plus controllers and persistence modules. Existing services can stay when they have coherent responsibilities. Preserve externally visible behavior unless a documented security fix requires a change. A file tree alone does not prove MVC; trace responsibilities and dependency direction after refactoring.
