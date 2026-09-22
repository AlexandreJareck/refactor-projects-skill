# Project analysis heuristics

Inspect manifests and lockfiles first, then entry points and imports. Python: `requirements.txt`, `pyproject.toml`, `app.py`, Blueprint registration and decorators reveal Flask and routes. Node.js: `package.json`, lockfile, `app.js`, `express()`, route methods and middleware reveal Express. Distinguish a declared version constraint from the version actually installed; report which source was used.

Find database technology through dependencies, connection setup, ORM initialization, schemas and query calls. Do not infer a production database merely from unused configuration values. Trace startup, seed behavior and table/model names. Identify the domain from route names, models and documented requests, not directory names alone.

Map the current dependency direction: HTTP route, controller or handler, business logic, persistence, and external services. Look for layers that already exist and whether their contents match their names. Record source file count with a stated rule, and inventory method/path pairs including administrative and health routes. Use isolated databases or fixtures for baseline calls; do not send destructive requests to a shared database. Capture status and safe response shape for successful and invalid requests. Mask credentials, cards and tokens in logs.
